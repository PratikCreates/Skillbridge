import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
from typing import List, Dict, Any

from .models import Skill, SkillRelationship

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_skills(self, skill_data: List[Dict[str, Any]], embeddings: Dict[str, List[float]]) -> Dict[str, int]:
        """
        Performs a bulk "upsert" operation for skills. It efficiently inserts new
        skills or updates existing ones in a single database round-trip.
        """
        skills_to_upsert = []
        for skill_info in skill_data:
            skill_name = skill_info.get("name")
            if not skill_name:
                continue
            
            skill_embedding = embeddings.get(skill_name)
            
            skills_to_upsert.append({
                "name": skill_name,
                "category": skill_info.get("category"),
                "description": f"Skill: {skill_name}",
                # Only include embedding if it exists to avoid inserting None
                **({"skill_embedding": skill_embedding} if skill_embedding else {})
            })
        
        if not skills_to_upsert:
            return {}

        logger.info(f"Upserting {len(skills_to_upsert)} skills into the database.")
        
        # Create the bulk UPSERT statement
        stmt = insert(Skill).values(skills_to_upsert)
        
        # Define what to update if a skill with the same unique name already exists
        update_stmt = stmt.on_duplicate_key_update(
            category=stmt.inserted.category,
            # Only update the embedding if a new one is provided
            skill_embedding=stmt.inserted.skill_embedding
        )
        
        self.session.execute(update_stmt)
        self.session.commit()
        
        # Now that all skills are guaranteed to be in the DB, fetch their IDs
        skill_names = [s['name'] for s in skills_to_upsert]
        result = self.session.query(Skill.id, Skill.name).filter(Skill.name.in_(skill_names)).all()
        
        skill_map = {name: id for id, name in result}
        return skill_map

    def insert_skill_relationships(self, skill_data: List[Dict[str, Any]], skill_map: Dict[str, int]):
        """
        Performs a bulk upsert of prerequisite relationships based on LLM-generated data.
        """
        relationships_to_insert = []
        for skill_info in skill_data:
            source_skill_name = skill_info.get("name")
            source_id = skill_map.get(source_skill_name)
            
            # Ensure prerequisites is a list to prevent errors
            prerequisites = skill_info.get("prerequisites", [])
            if not isinstance(prerequisites, list):
                continue
            
            for prereq_name in prerequisites:
                target_id = skill_map.get(prereq_name)
                # Only create a relationship if both skills exist in our map
                if source_id and target_id:
                    relationships_to_insert.append({
                        "source_skill_id": source_id,
                        "target_skill_id": target_id,
                        "relationship_type": "PREREQUISITE",
                        "strength": 0.9,
                        "inference_source": "LLM_ANALYSIS" # Generalized source
                    })
        
        if not relationships_to_insert:
            return

        logger.info(f"Upserting {len(relationships_to_insert)} skill relationships.")
        
        # Create and execute the bulk UPSERT statement for relationships
        stmt = insert(SkillRelationship).values(relationships_to_insert)
        update_stmt = stmt.on_duplicate_key_update(
            strength=stmt.inserted.strength,
            inference_source=stmt.inserted.inference_source
        )
        self.session.execute(update_stmt)
        self.session.commit()