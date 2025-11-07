# skillbridge/processing/researcher_client.py (New File)

import openai
from skillbridge.utils.config import AIML_API_KEY, AIML_API_BASE
import logging

logger = logging.getLogger(__name__)

ai_client = openai.OpenAI(api_key=AIML_API_KEY, base_url=AIML_API_BASE)

def research_job_postings(role_title: str) -> str:
    """
    Uses a web-search-enabled LLM to act as a "Researcher Agent",
    finding and consolidating high-quality job descriptions.
    """
    logger.info(f"Researcher Agent starting search for '{role_title}' job postings...")
    
    prompt = f"""
    You are an AI Research Agent. Your task is to find 3 to 5 recent, high-quality, and detailed job descriptions for the role of '{role_title}'.
    Use your web search capabilities to find these postings on reputable job boards or company career pages.
    
    Once found, extract and combine the full text of these job descriptions.
    Separate each description with the delimiter "--- END OF POSTING ---".
    
    Return ONLY the combined text of the job descriptions and nothing else.
    """
    
    try:
        # Use a fast, search-enabled model for this research task.
        response = ai_client.chat.completions.create(
            model="google/gemini-2.0-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        combined_text = response.choices[0].message.content
        logger.info(f"Researcher Agent successfully gathered {len(combined_text.split('--- END OF POSTING ---'))} job postings.")
        return combined_text
    except Exception as e:
        logger.error(f"Researcher Agent failed for '{role_title}': {e}")
        return ""