from groq import AsyncGroq
import os
from dotenv import load_dotenv 
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env or environment variables.")
from groq import Groq
client = AsyncGroq(api_key=GROQ_API_KEY)
