import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL")

# --- AI APIs ---
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
AIML_API_KEY = os.getenv("AIML_API_KEY")
NEBIUS_KEY = os.getenv("NEBIUS_KEY")

# --- Modal ---
MODAL_WEB_URL = os.getenv("MODAL_WEB_URL")

# --- External Data Sources ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# --- AIML API Configuration ---
AIML_API_BASE = "https://api.aimlapi.com/v1"

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
STACKEXCHANGE_API_KEY = os.getenv("STACKEXCHANGE_API_KEY")