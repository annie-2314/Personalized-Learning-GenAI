import os
# from groq import Groq
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Missing GROQ_API_KEY in environment.")

client = AsyncGroq(api_key=api_key)
