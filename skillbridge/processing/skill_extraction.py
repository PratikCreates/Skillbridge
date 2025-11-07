import openai
import spacy
from spacy.matcher import PhraseMatcher
from typing import List, Dict, Any
import base64
import json
import logging
import re

from skillbridge.utils.config import AIML_API_KEY, AIML_API_BASE
from skillbridge.database.models import Skill, SkillAlias
from skillbridge.database.connection import SessionLocal
from .skills_db import SKILL_DB

logger = logging.getLogger(__name__)

# --- UNIFIED AIML API CLIENT ---
# This single client is used for both embeddings and user-facing reasoning.
ai_client = openai.OpenAI(api_key=AIML_API_KEY, base_url=AIML_API_BASE)

class NLPEngine:
    """A spaCy-based engine that dynamically loads its skill dictionary."""
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._load_skills_from_db_and_static()

    def _load_skills_from_db_and_static(self):
        logger.info("NLPEngine: Loading skills from static file and database...")
        session = SessionLocal()
        try:
            # 1. Start with the static SKILL_DB as a reliable base.
            skill_dict = {k: [alias.lower() for alias in v] for k, v in SKILL_DB.items()}

            # 2. Query the database for all skills and approved aliases.
            db_skills = session.query(Skill).all()
            approved_aliases = (
                session.query(Skill.name, SkillAlias.alias)
                .join(SkillAlias, Skill.id == SkillAlias.skill_id)
                .filter(SkillAlias.status == 'APPROVED')
                .all()
            )
            
            # 3. Merge the database knowledge into our dictionary.
            for skill in db_skills:
                if skill.name not in skill_dict: skill_dict[skill.name] = [skill.name.lower()]
            for canonical_name, alias in approved_aliases:
                if canonical_name in skill_dict and alias.lower() not in skill_dict[canonical_name]:
                    skill_dict[canonical_name].append(alias.lower())

            # 4. Build the final matcher from the complete, merged dictionary.
            for canonical_name, alias_list in skill_dict.items():
                patterns = [self.nlp.make_doc(text) for text in set(alias_list)]
                self.matcher.add(canonical_name, patterns)
            
            logger.info(f"NLPEngine: Successfully loaded {len(skill_dict)} canonical skills.")
        finally:
            session.close()

    def extract_known_skills(self, text: str) -> List[str]:
        doc = self.nlp(text)
        matches = self.matcher(doc)
        return list({self.nlp.vocab.strings[match_id] for match_id, start, end in matches})


def get_embedding(text: str, model="text-embedding-ada-002") -> List[float]:
    """Generates embeddings using the AIML API client."""
    text = text.replace("\n", " ")
    try:
        response = ai_client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        return []

def robust_json_parser(text: str) -> dict:
    """
    A robust parser that finds and extracts the first valid JSON object
    from a string, ignoring any extra text before or after it.
    """

    # Find the start of the first JSON object '{' and the end of the last '}'
    start_index = text.find('{')
    end_index = text.rfind('}')
    
    if start_index == -1 or end_index == -1:
        logger.error("Robust parser could not find a JSON object in the LLM response.")
        return {}
        
    json_str = text[start_index : end_index + 1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Robust JSON parsing failed even after extraction: {e}")
        logger.debug(f"Problematic JSON string: {json_str}")
        return {}

def supervise_and_discover_with_llm(text: str, found_skills: List[str]) -> Dict[str, Any]:
    """Uses a cost-effective model from AIML API with robust encoding and parsing."""
    encoded_text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    prompt = f"""
    You are an AI Analyst. A fast NLP model found these potential skills: {json.dumps(found_skills)}.
    Your task is to analyze the full resume text provided below in Base64 format.
    
    Instructions:
    1. Decode the Base64 text.
    2. Validate found skills and discover any missed technical skills.
    3. Structure the output as a JSON object with a "skills" key, containing a list of objects (each with "name", "category", "prerequisites").

    Base64-Encoded Text: --- {encoded_text} ---
    
    Respond with ONLY the valid JSON object.
    """
    try:
        response = ai_client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_content = response.choices[0].message.content
        
        # --- THIS IS THE FIX ---
        # Instead of a direct json.loads, use our new robust parser.
        return robust_json_parser(raw_content)

    except Exception as e:
        logger.error(f"LLM supervision with AIML API failed: {e}")
        return {"skills": []}

def process_text_for_skills(text: str) -> Dict[str, Any]:
    """The full hybrid skill extraction pipeline for user-facing requests."""
    nlp_engine = NLPEngine()
    known_skills = nlp_engine.extract_known_skills(text)
    
    validated_data = supervise_and_discover_with_llm(text, known_skills)
    
    final_skills = validated_data.get("skills", [])
    if not final_skills:
        # Return an empty result but log that no skills were found
        logger.warning("Supervision step returned no valid skills from the resume text.")
        return {"skills": [], "embeddings": {}}

    embeddings = {
        skill.get("name"): get_embedding(skill.get("name"))
        for skill in final_skills if skill.get("name")
    }
    return {"skills": final_skills, "embeddings": embeddings}