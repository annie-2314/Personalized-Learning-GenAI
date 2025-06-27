# app/services/groq_client.py

import os
from groq import AsyncGroq # Ensure you are importing AsyncGroq

# Attempt to get API key from Streamlit secrets or environment variable
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Check Streamlit secrets if not found in environment variables
if not GROQ_API_KEY and "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it as an environment variable or in Streamlit secrets.")

# Initialize the asynchronous Groq client
client = AsyncGroq(
    api_key=GROQ_API_KEY,
)
