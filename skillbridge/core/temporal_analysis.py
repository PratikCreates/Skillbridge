import logging
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
from datetime import date

# Centralize imports at the top of the file
from skillbridge.database.models import Skill, TemporalSkillTrend
from skillbridge.processing.external_apis import StackOverflowClient, RedditClient

logger = logging.getLogger(__name__)

class TemporalAnalysisEngine:
    def __init__(self, session: Session):
        self.session = session
        self.so_client = StackOverflowClient()
        self.reddit_client = RedditClient()
        
    def gather_and_store_trends(self):
        """
        Gets all skills from the DB, queries external APIs for their current
        popularity, and stores the results in batches to prevent database overload.
        """
        logger.info("Starting weekly trend analysis...")
        
        skills = self.session.query(Skill).all()
        if not skills:
            logger.warning("No skills found in the database. Aborting trend analysis.")
            return

        trends_to_store = []
        today = date.today()

        logger.info(f"Gathering trends for {len(skills)} skills...")
        for skill in skills:
            # Gather data from Stack Overflow
            so_score = self.so_client.get_skill_trend_score(skill.name)
            if so_score > 0:
                trends_to_store.append({
                    "skill_id": skill.id, "record_date": today,
                    "metric_source": "STACKOVERFLOW", "value": so_score
                })
            
            # Gather data from Reddit (using a job-focused subreddit)
            reddit_score = self.reddit_client.get_skill_trend_score(skill.name, subreddit="forhire")
            if reddit_score > 0:
                trends_to_store.append({
                    "skill_id": skill.id, "record_date": today,
                    "metric_source": "REDDIT_JOBS", "value": reddit_score
                })
        
        if not trends_to_store:
            logger.info("No new trend data was gathered. Trend analysis complete.")
            return
        
        # --- Batch Processing to Handle Large Data Volumes ---
        # This prevents "Lost connection" errors by breaking the large INSERT
        # statement into smaller, manageable chunks.
        batch_size = 100
        total_stored = 0
        
        logger.info(f"Storing {len(trends_to_store)} new trend records in batches of {batch_size}...")
        
        for i in range(0, len(trends_to_store), batch_size):
            batch = trends_to_store[i:i + batch_size]
            if not batch:
                continue
            
            try:
                stmt = insert(TemporalSkillTrend).values(batch)
                # If a record for this skill/date/source already exists, update its value.
                update_stmt = stmt.on_duplicate_key_update(value=stmt.inserted.value)
                
                self.session.execute(update_stmt)
                self.session.commit()
                
                total_stored += len(batch)
                logger.info(f"Successfully stored batch #{i//batch_size + 1}. Total stored: {total_stored}")
            except Exception as e:
                logger.error(f"Error storing batch #{i//batch_size + 1}: {e}")
                # Rollback the failed batch and continue with the next one.
                self.session.rollback()
                continue
        
        logger.info(f"Trend data storage complete. Stored {total_stored} of {len(trends_to_store)} gathered records.")