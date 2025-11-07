import openai
from skillbridge.utils.config import NEBIUS_KEY
import logging

logger = logging.getLogger(__name__)

class NebiusClient:
    def __init__(self):
        if not NEBIUS_KEY:
            self.client = None
            logger.warning("NEBIUS_KEY not found. NebiusClient will be disabled.")
        else:
            self.client = openai.OpenAI(
                api_key=NEBIUS_KEY,
                # --- THIS IS THE FIX ---
                # The base URL should NOT include the '/chat' endpoint.
                # The OpenAI library adds that part automatically.
                base_url="https://api.studio.nebius.ai/v1",
            )
    
    def analyze_with_sota_model(self, prompt: str):
        """Uses the state-of-the-art Kimi-K2 Instruct model on Nebius."""
        if not self.client:
            raise Exception("Nebius client is not initialized.")
            
        try:
            response = self.client.chat.completions.create(
                model="moonshotai/Kimi-K2-Instruct",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Nebius SOTA API call failed: {e}")
            raise