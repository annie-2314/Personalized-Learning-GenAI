import os
# import streamlit as st # <-- Optionally remove this if 'st' is truly not used elsewhere in THIS specific file
from dotenv import load_dotenv # <-- Make sure this line is here

# Load environment variables from the .env file.
# This must be called BEFORE you try to access os.getenv for .env variables.
load_dotenv()

# Get the API key from environment variables.
# This will now successfully read from your .env file after load_dotenv().
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Check if the key was actually loaded.
# We are explicitly REMOVING the 'in st.secrets' check.
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env or environment variables.")

from groq import Groq

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)