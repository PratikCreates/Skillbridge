import logging
import networkx as nx
from sqlalchemy.orm import Session
from collections import defaultdict

from skillbridge.database.models import Skill, SkillRelationship
from skillbridge.processing.external_apis import StackOverflowClient

logger = logging.getLogger(__name__)

class GraphValidator:
    def __init__(self, session: Session):
        self.session = session
        self.so_client = StackOverflowClient()
        self.graph = nx.DiGraph()
        self._load_full_graph()

    def _load_full_graph(self):
        """Loads the entire skill graph, including relationship IDs."""
        skills = self.session.query(Skill).all()
        skill_id_to_name = {skill.id: skill.name for skill in skills}

        relationships = self.session.query(SkillRelationship)\
            .filter(SkillRelationship.relationship_type == 'PREREQUISITE').all()
        
        for rel in relationships:
            source_name = skill_id_to_name.get(rel.source_skill_id)
            target_name = skill_id_to_name.get(rel.target_skill_id)
            if source_name and target_name:
                # Store the relationship ID on the edge for easy updates
                self.graph.add_edge(target_name, source_name, rel_id=rel.id)

    def validate_and_score_relationships(self):
        """
        Runs the full validation pipeline: cycle detection and community validation.
        """
        logger.info("Starting graph validation and confidence scoring...")
        
        # 1. Self-Correction: Penalize cycles
        self._penalize_cycles()
        
        # 2. Community Validation: Use Stack Overflow to score links
        self._validate_with_community_data()
        
        logger.info("Graph validation and scoring complete.")

    def _penalize_cycles(self):
        """Finds and penalizes circular dependencies in the graph."""
        cycles = list(nx.simple_cycles(self.graph))
        if not cycles:
            logger.info("No circular dependencies found in the graph. Excellent!")
            return

        logger.warning(f"Found {len(cycles)} circular dependencies. Penalizing confidence scores.")
        rel_ids_to_penalize = set()
        for cycle in cycles:
            # Find the relationship IDs for each edge in the cycle
            for i in range(len(cycle)):
                u = cycle[i]
                v = cycle[(i + 1) % len(cycle)]
                if self.graph.has_edge(u, v):
                    rel_ids_to_penalize.add(self.graph[u][v]['rel_id'])
        
        if rel_ids_to_penalize:
            self.session.query(SkillRelationship)\
                .filter(SkillRelationship.id.in_(rel_ids_to_penalize))\
                .update({"confidence_score": 0.1}, synchronize_session=False) # Drastically reduce confidence
            self.session.commit()
            logger.info(f"Penalized {len(rel_ids_to_penalize)} relationships involved in cycles.")

    def _validate_with_community_data(self):
        """
        Uses Stack Overflow tag counts to validate prerequisite links.
        Hypothesis: If 'Python' is a prerequisite for 'PyTorch', then the count of
        'PyTorch' tags should be less than or equal to the count of 'Python' tags.
        """
        logger.info("Performing community validation using Stack Overflow data...")
        relationships = self.session.query(SkillRelationship).filter(SkillRelationship.relationship_type == 'PREREQUISITE').all()
        skills_to_query = {rel.source_skill_id for rel in relationships} | {rel.target_skill_id for rel in relationships}
        
        skill_scores = {}
        for skill_id in skills_to_query:
            skill_name = self.session.query(Skill.name).filter(Skill.id == skill_id).scalar()
            if skill_name:
                skill_scores[skill_id] = self.so_client.get_skill_trend_score(skill_name)
        
        for rel in relationships:
            source_score = skill_scores.get(rel.source_skill_id, 0)
            target_score = skill_scores.get(rel.target_skill_id, 0)
            
            # If the prerequisite (target) is MORE popular than the skill (source), it's a good sign.
            if target_score > source_score:
                rel.confidence_score = min(1.0, rel.confidence_score + 0.1) # Boost confidence
            # If the skill is more popular than its supposed prerequisite, it's a weak sign.
            elif source_score > target_score:
                rel.confidence_score = max(0.1, rel.confidence_score - 0.1) # Slightly reduce confidence
        
        self.session.commit()
        logger.info("Community validation complete. Confidence scores updated.")