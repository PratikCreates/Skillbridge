import logging
import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session
from sqlalchemy import desc
from skillbridge.database.models import Skill, TemporalSkillTrend

logger = logging.getLogger(__name__)

class PredictionEngine:
    def __init__(self, session: Session):
        self.session = session

    def forecast_skill_trend(self, skill_name: str) -> dict:
        """
        Forecasts the future trend of a skill, with a robust fallback for new skills.
        """
        logger.info(f"Forecasting trend for skill: '{skill_name}'")
        
        history_query = self.session.query(
            TemporalSkillTrend.record_date,
            TemporalSkillTrend.value
        ).join(Skill, Skill.id == TemporalSkillTrend.skill_id)\
         .filter(Skill.name == skill_name)\
         .filter(TemporalSkillTrend.metric_source == 'STACKOVERFLOW')\
         .order_by(TemporalSkillTrend.record_date.asc())
        
        history_df = pd.DataFrame(history_query.all(), columns=['ds', 'y'])

        # --- THIS IS THE FIX ---
        # If there is not enough data for a forecast, just return the latest known score.
        if len(history_df) < 2:
            logger.warning(f"Not enough historical data for '{skill_name}'. Falling back to latest score.")
            latest_score = 0
            if not history_df.empty:
                latest_score = int(history_df['y'].iloc[-1])
            
            return {
                "current_score": latest_score,
                "predicted_score_6m": latest_score, # Predict no change
                "growth_percentage": 0.0,
                "forecast_successful": False # Flag that this is not a real forecast
            }

        # If we have enough data, proceed with the Prophet forecast
        model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        model.fit(history_df)
        future = model.make_future_dataframe(periods=180)
        forecast = model.predict(future)
        
        current_score = int(history_df['y'].iloc[-1])
        predicted_score = int(forecast['yhat'].iloc[-1])
        growth = ((predicted_score - current_score) / current_score) * 100 if current_score > 0 else 0.0

        return {
            "current_score": current_score,
            "predicted_score_6m": predicted_score,
            "growth_percentage": round(growth, 2),
            "forecast_successful": True
        }