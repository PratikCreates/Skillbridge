import logging
from sqlalchemy.orm import Session
from skillbridge.core.prediction_engine import PredictionEngine
from skillbridge.processing.external_apis import StackOverflowClient # Crucial for the fallback

logger = logging.getLogger(__name__)

class SkillAnalysisEngine:
    def __init__(self, session: Session, so_client: StackOverflowClient):
        """
        Initializes the engine with a database session and a StackOverflow client
        for the real-time fallback mechanism.
        """
        self.session = session
        self.prediction_engine = PredictionEngine(session)
        # --- THIS IS THE FIX ---
        # The engine needs the so_client for its real-time fallback.
        self.so_client = so_client

    def analyze_skills(self, user_skills: list[str], target_skills: list[str]) -> dict:
        """
        Performs a gap analysis and enriches it with predictive forecasting,
        including a real-time fallback for new skills.
        """
        logger.info("Starting skill analysis with predictive forecasting...")
        report = {"required_skills": []}
        user_skills_set = set(s.lower() for s in user_skills)

        for skill_name in target_skills:
            has_skill = skill_name.lower() in user_skills_set
            
            # 1. First, try to get a forecast from our historical data.
            forecast_data = self.prediction_engine.forecast_skill_trend(skill_name)
            
            current_score = forecast_data["current_score"]
            
            # --- THIS IS THE FIX ---
            # 2. If the score is zero (because it's a new skill with no history),
            #    perform a live, real-time query to Stack Overflow.
            if current_score == 0:
                logger.warning(f"No historical trend data for '{skill_name}'. Using real-time fallback.")
                real_time_score = self.so_client.get_skill_trend_score(skill_name)
                if real_time_score > 0:
                    current_score = real_time_score
                    forecast_data["current_score"] = real_time_score
            
            skill_info = {
                "skill_name": skill_name,
                "user_has_skill": has_skill,
                "market_demand_score": forecast_data["current_score"],
                "predicted_demand_6m": forecast_data["predicted_score_6m"],
                "growth_percentage": forecast_data["growth_percentage"],
                "is_trending": forecast_data["growth_percentage"] > 5
            }
            report["required_skills"].append(skill_info)
        
        report["required_skills"].sort(key=lambda x: x["market_demand_score"], reverse=True)
        return report