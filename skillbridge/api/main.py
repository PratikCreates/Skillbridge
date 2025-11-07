import modal
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = modal.App("skillbridge-ai-career-api-v3")

image = (
    modal.Image.from_registry("python:3.10")
    .pip_install_from_requirements("requirements.txt")
    .run_commands("python -m spacy download en_core_web_sm")
    .add_local_python_source("skillbridge")
    .add_local_file(local_path="isrgrootx1.pem", remote_path="/root/isrgrootx1.pem")
)

secrets = [modal.Secret.from_dotenv()]

def _create_tables_if_needed():
    from skillbridge.database.models import Base
    from skillbridge.database.connection import engine
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}"); raise

@app.function(image=image, secrets=secrets, retries=2, timeout=600)
def process_resume_and_generate_path(file_content: bytes, filename: str, target_role: str):
    """The complete orchestration function for a user's career analysis request."""
    from skillbridge.processing.resume_parser import parse_resume
    from skillbridge.processing.skill_extraction import process_text_for_skills
    from skillbridge.database.connection import SessionLocal
    from skillbridge.database.db_service import DatabaseService
    from skillbridge.database.models import Skill, RoleSkillRequirement, TargetRole
    from skillbridge.core.career_graph import CareerPathGenerator
    from skillbridge.core.resource_matcher import ResourceMatcher
    from skillbridge.core.skill_analysis import SkillAnalysisEngine
    from skillbridge.processing.external_apis import StackOverflowClient # Ensure this is imported

    _create_tables_if_needed()
    text = parse_resume(file_content, filename)
    if not text.strip(): return {"error": "No text could be extracted."}
    
    processed_data = process_text_for_skills(text)
    extracted_skills_info = processed_data.get("skills", [])
    if not extracted_skills_info: return {"error": "AI could not extract any meaningful skills."}
    
    session = SessionLocal()
    try:
        db_service = DatabaseService(session)
        skill_map = db_service.get_or_create_skills(extracted_skills_info, {})
        current_user_skills = list(skill_map.keys())

        target_skills_query = session.query(Skill.name).join(RoleSkillRequirement).join(TargetRole).filter(TargetRole.name == target_role)
        target_skills = [s[0] for s in target_skills_query.all()]
        if not target_skills: return {"error": f"Role '{target_role}' has no defined skills. Please run the AI Surfer."}

        path_generator = CareerPathGenerator(session)
        path_result = path_generator.generate_path(current_user_skills, target_skills)
        
        learning_resources = []
        if path_result.get("path"):
            path_skill_objects = session.query(Skill).filter(Skill.name.in_(path_result["path"])).all()
            skill_details_for_matcher = [{"name": s.name, "keywords": s.description.split(", ") if s.description else [s.name]} for s in path_skill_objects]
            resource_matcher = ResourceMatcher()
            learning_resources = resource_matcher.get_resources_for_path(skill_details_for_matcher)

        # --- THIS IS THE DEFINITIVE FIX ---
        # The SkillAnalysisEngine requires the so_client for its real-time fallback.
        so_client = StackOverflowClient()
        analysis_engine = SkillAnalysisEngine(session, so_client=so_client) 
        skill_analysis_report = analysis_engine.analyze_skills(current_user_skills, target_skills)

        return {
            "extracted_skills": current_user_skills, "target_role": target_role,
            "learning_path": path_result, "learning_resources": learning_resources,
            "skill_analysis_report": skill_analysis_report,
        }
    finally:
        session.close()

@app.cls(image=image, secrets=secrets)
class API:
    @modal.asgi_app()
    def web_app(self):
        from fastapi import FastAPI, UploadFile, File, Form, Response
        from fastapi.responses import JSONResponse
        fastapi_app = FastAPI()

        @fastapi_app.post("/analyze_career")
        async def analyze_career(target_role: str = Form(...), file: UploadFile = File(...)):
            content = await file.read(); call = process_resume_and_generate_path.spawn(content, file.filename, target_role)
            return JSONResponse({"call_id": call.object_id})

        @fastapi_app.get("/get_result")
        def get_result(call_id: str):
            from modal.functions import FunctionCall
            try:
                call = FunctionCall.from_id(call_id)
                try: return call.get(timeout=0)
                except TimeoutError: return JSONResponse({"status": "running"})
            except Exception as e: return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

        @fastapi_app.get("/get_roles")
        def get_roles():
            from skillbridge.database.connection import SessionLocal
            from skillbridge.database.models import TargetRole
            session = SessionLocal()
            try:
                roles = session.query(TargetRole.name).order_by(TargetRole.name).all()
                return {"roles": [role[0] for role in roles]}
            finally: session.close()

        @fastapi_app.get("/get_skill_graph")
        def get_skill_graph():
            from skillbridge.database.connection import SessionLocal
            from skillbridge.database.models import Skill, SkillRelationship
            session = SessionLocal()
            try:
                relationships = session.query(SkillRelationship.source_skill_id, SkillRelationship.target_skill_id).filter(SkillRelationship.relationship_type == 'PREREQUISITE').all()
                skill_ids = {rel.source_skill_id for rel in relationships} | {rel.target_skill_id for rel in relationships}
                skills = session.query(Skill.id, Skill.name).filter(Skill.id.in_(skill_ids)).all()
                id_to_name = {id: name for id, name in skills}
                edges = [[id_to_name.get(rel.target_skill_id), id_to_name.get(rel.source_skill_id)] for rel in relationships if id_to_name.get(rel.source_skill_id) and id_to_name.get(rel.target_skill_id)]
                return {"edges": edges}
            finally: session.close()

        @fastapi_app.get("/find_deeper_prereqs")
        def find_deeper_prereqs(skill_name: str):
            from openai import OpenAI
            from skillbridge.utils.config import AIML_API_KEY, AIML_API_BASE
            ai_client = OpenAI(api_key=AIML_API_KEY, base_url=AIML_API_BASE)
            prompt = f"What are 2-3 fundamental, beginner-level prerequisites for learning '{skill_name}'? Focus on concepts. Return a JSON object with a single key 'prerequisites' which is a list of strings."
            try:
                response = ai_client.chat.completions.create(model="mistralai/Mistral-7B-Instruct-v0.3", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.0)
                return json.loads(response.choices[0].message.content)
            except Exception as e: return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
            
        return fastapi_app

# --- SCHEDULED FUNCTIONS ---
@app.function(image=image, secrets=secrets, schedule=modal.Cron("0 2 * * *"), timeout=1800)
def run_daily_knowledge_graph_update():
    from skillbridge.core.knowledge_graph_builder import KnowledgeGraphBuilder
    from skillbridge.database.connection import SessionLocal
    logger.info("--- Starting Job: AI Surfer ---")
    _create_tables_if_needed()
    ROLES_TO_SURF = ["Data Scientist", "Frontend Developer", "AI Engineer", "Cloud Architect", "Data Engineer", "Cybersecurity Analyst"]
    session = SessionLocal()
    try:
        builder = KnowledgeGraphBuilder(session)
        for role in ROLES_TO_SURF: builder.update_role_requirements(role)
        logger.info("--- Job COMPLETED: AI Surfer ---")
    except Exception as e: logger.error(f"--- ERROR in AI Surfer Job: {e} ---")
    finally: session.close()

@app.function(image=image, secrets=secrets, schedule=modal.Cron("0 0 * * 1"), timeout=900)
def run_weekly_trend_analysis():
    from skillbridge.core.temporal_analysis import TemporalAnalysisEngine
    from skillbridge.database.connection import SessionLocal
    logger.info("--- Starting Job: Weekly Trend Analysis ---")
    _create_tables_if_needed()
    session = SessionLocal()
    try:
        engine = TemporalAnalysisEngine(session)
        engine.gather_and_store_trends()
        logger.info("--- Job COMPLETED: Weekly Trend Analysis ---")
    except Exception as e: logger.error(f"--- ERROR in Weekly Trend Analysis Job: {e} ---")
    finally: session.close()

@app.function(image=image, secrets=secrets, schedule=modal.Cron("0 3 * * 2"), timeout=1200)
def run_weekly_graph_validation():
    from skillbridge.core.graph_validator import GraphValidator
    from skillbridge.database.connection import SessionLocal
    logger.info("--- Starting Job: Guardian Graph Validation ---")
    _create_tables_if_needed()
    session = SessionLocal()
    try:
        validator = GraphValidator(session)
        validator.validate_and_score_relationships()
        logger.info("--- Job COMPLETED: Guardian Validation ---")
    except Exception as e: logger.error(f"--- ERROR in Guardian Job: {e} ---")
    finally: session.close()