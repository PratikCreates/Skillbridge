# skillbridge/core/knowledge_graph_builder.py (Complete Final Version)

import logging
import json
from sqlalchemy.orm import Session

# --- PIVOT: Import our new, specialized AI clients ---
from skillbridge.processing.researcher_client import research_job_postings
from skillbridge.processing.nebius_client import NebiusClient 

from skillbridge.database.db_service import DatabaseService
from skillbridge.database.models import TargetRole, RoleSkillRequirement, Skill

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    def __init__(self, session: Session):
        self.session = session
        self.db_service = DatabaseService(session)
        # The "Expert Analyst" agent, using our most powerful model on Nebius
        self.analyst_client = NebiusClient()

    def update_role_requirements(self, role_title: str):
        logger.info(f"AI Surfer starting two-agent analysis for role: '{role_title}'")
        
        # --- SOTA WORKFLOW STEP 1: RESEARCH ---
        # Use the "Researcher Agent" (Gemini on AIML) to gather high-quality data.
        combined_text = research_job_postings(role_title)
        if not combined_text:
            logger.warning(f"Researcher Agent found no data for '{role_title}'. Aborting.")
            return

        # --- SOTA WORKFLOW STEP 2: ANALYSIS ---
        # Use the "Expert Analyst Agent" (Hermes on Nebius) for deep processing.
        prompt = f"""
        You are an expert HR Technology Analyst building a hierarchical skill knowledge graph.
        Analyze the following job descriptions for the role of '{role_title}'.

        Your instructions are:
        1.  **Extract Core Skills**: Identify ONLY the 5-7 MOST CRITICAL, non-overlapping, high-level technical skills.
        2.  **Normalize Names**: Standardize all skill names (e.g., "React.js" -> "React").
        3.  **Find Search Keywords**: For each core skill, provide a list of 2-3 specific, high-quality search keywords for YouTube/GitHub.
        4.  **Establish Prerequisites**: For each core skill, identify its immediate prerequisite FROM WITHIN THE EXTRACTED LIST.

        Return your analysis as a single JSON object with a "skills" key. The value is a list of objects, each with "name", "keywords", and "prerequisites".
        
        --- JOB DESCRIPTIONS TEXT ---
        {combined_text}
        """
        
        try:
            raw_response = self.analyst_client.analyze_with_sota_model(prompt)
            extracted_data = json.loads(raw_response)
            skills_with_details = extracted_data.get("skills", [])

            if not skills_with_details:
                logger.warning(f"Expert Analyst Agent extracted no skills for '{role_title}'.")
                return
            
            logger.info(f"Expert Analyst (Hermes) extracted {len(skills_with_details)} SOTA skills for '{role_title}'.")
            
            # The rest of the database logic is correct and handles this new structure.
            role_obj = self.session.query(TargetRole).filter_by(name=role_title).first()
            if not role_obj:
                role_obj = TargetRole(name=role_title)
                self.session.add(role_obj)
                self.session.commit()
            
            # Note: The `get_or_create_skills` expects dicts with a "name" key.
            # `skills_with_details` is already in the correct format.
            skill_map = self.db_service.get_or_create_skills(skills_with_details, {})
            self.db_service.insert_skill_relationships(skills_with_details, skill_map)
            
            # Overwrite existing role requirements with the new, high-quality list
            self.session.query(RoleSkillRequirement).filter_by(role_id=role_obj.id).delete()
            self.session.commit() # Commit the deletion before adding new ones
            for skill_id in skill_map.values():
                self.session.merge(RoleSkillRequirement(role_id=role_obj.id, skill_id=skill_id))
            
            self.session.commit()
            logger.info(f"Successfully updated knowledge graph for role '{role_title}'.")
        except Exception as e:
            logger.error(f"Expert Analyst Agent failed for '{role_title}': {e}")
            self.session.rollback()