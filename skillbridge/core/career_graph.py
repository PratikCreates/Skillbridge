import networkx as nx
from typing import List, Dict
from sqlalchemy.orm import Session
import logging

# We only need to import the models directly for querying
from skillbridge.database.models import Skill, SkillRelationship

logger = logging.getLogger(__name__)

class CareerPathGenerator:
    def __init__(self, session: Session):
        self.session = session
        self.graph = nx.DiGraph()
        self._load_skill_graph()

    def _load_skill_graph(self):
        """
        Loads all skills and their prerequisite relationships into a directed graph
        using efficient, joined queries.
        """
        logger.info("Loading skill knowledge graph into memory...")

        # More efficient: Query all skills and relationships at once.
        skills = self.session.query(Skill).all()
        skill_id_to_name = {skill.id: skill.name for skill in skills}

        for skill in skills:
            self.graph.add_node(skill.name, category=skill.category)

        # --- THIS IS THE FIX ---
        # Only load relationships where the confidence_score is above 0.3
        relationships = self.session.query(SkillRelationship)\
            .filter(SkillRelationship.relationship_type == 'PREREQUISITE')\
            .filter(SkillRelationship.confidence_score > 0.3).all()  # Confidence filter applied
        
        edge_count = 0
        for rel in relationships:
            source_name = skill_id_to_name.get(rel.source_skill_id)
            target_name = skill_id_to_name.get(rel.target_skill_id)

            # The edge means source_skill is a prerequisite for target_skill.
            # So, the learning path flows from source -> target.
            if source_name and target_name:
                # Add the confidence as an edge weight
                self.graph.add_edge(source_name, target_name, weight=rel.confidence_score)
                edge_count += 1

        logger.info(f"Knowledge graph loaded: {self.graph.number_of_nodes()} nodes, {edge_count} prerequisite edges.")

    def generate_path(self, current_skills: List[str], target_skills: List[str]) -> Dict:
        """
        Generates a learning path with inference to avoid suggesting skills
        the user implicitly knows.
        """
        logger.info("Generating inference-aware learning path...")

        # 1. Infer skills the user implicitly knows, but be conservative about fundamentals
        implied_skills = set()
        current_skills_set = set(current_skills)
        
        # Define skills that should NOT be auto-inferred (fundamentals that people often skip)
        # These are skills that people commonly learn out of order or skip
        fundamental_skills = {"HTML", "CSS", "SQL", "Linux", "Git", "Command Line", "Networking"}
        
        for skill in current_skills_set:
            if self.graph.has_node(skill):
                # Get all prerequisites, but filter out fundamentals unless explicitly stated
                ancestors = nx.ancestors(self.graph, skill)
                
                # Only infer non-fundamental skills or fundamentals with high confidence
                for ancestor in ancestors:
                    if ancestor not in fundamental_skills:
                        implied_skills.add(ancestor)
                    else:
                        # For fundamentals, only infer if there's a very strong relationship
                        if self.graph.has_edge(ancestor, skill):
                            edge_data = self.graph.get_edge_data(ancestor, skill)
                            weight = edge_data.get('weight', 0.5) if edge_data else 0.5
                            # Only infer fundamentals with very high confidence (>0.9)
                            if weight > 0.9:
                                implied_skills.add(ancestor)

        full_known_skills = current_skills_set | implied_skills
        logger.info(f"User has {len(current_skills_set)} explicit skills and {len(implied_skills)} implied skills.")

        # 2. Find all prerequisites required for the target skills.
        all_prerequisites = set()
        target_skills_set = set(target_skills)
        for skill in target_skills_set:
            if self.graph.has_node(skill):
                ancestors = nx.ancestors(self.graph, skill)
                all_prerequisites.update(ancestors)

        # 3. Determine the actual skill gaps.
        required_knowledge_set = all_prerequisites | target_skills_set
        skills_to_learn = required_knowledge_set - full_known_skills

        logger.info(f"Identified {len(skills_to_learn)} skill gaps.")

        if not skills_to_learn:
            return {"path": [], "message": "You already possess all the necessary skills!"}

        # 4. Generate the ordered learning path using topological sort.
        # Create a subgraph that includes all skills to learn, even if they're isolated
        subgraph = self.graph.subgraph(skills_to_learn).copy()
        
        # Add any missing skills as isolated nodes (skills that exist in target but not in graph)
        for skill in skills_to_learn:
            if skill not in subgraph:
                subgraph.add_node(skill)
        
        try:
            learning_path = list(nx.topological_sort(subgraph))
            logger.info(f"Generated ordered learning path of {len(learning_path)} steps.")
            return {"path": learning_path, "message": "Successfully generated learning path."}
        except nx.NetworkXUnfeasible:
            # This happens if there's a cycle in the prerequisite data (e.g., A -> B and B -> A).
            # We return the unordered list as a safe fallback.
            logger.warning("Circular dependency detected in skill gaps. Returning unordered list.")
            return {"path": list(skills_to_learn), "error": "Circular dependency found, returning unordered list."}
