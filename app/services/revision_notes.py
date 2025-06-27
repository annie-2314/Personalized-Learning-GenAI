# app/services/revision_notes.py

import os
# from groq import Groq # REMOVE this line
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
import asyncio # Add this import for async operations if not already there

# Import the shared async Groq client
from .groq_client import client as groq_async_client # Correct import for shared async client

# --- REMOVE DUPLICATE API KEY HANDLING AND CLIENT INITIALIZATION ---
# GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# if not GROQ_API_KEY and "GROQ_API_KEY" in st.secrets:
#     GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
# client = Groq(api_key=GROQ_API_KEY,)
# -------------------------------------------------------------------

# Define your prompt templates
QUICK_SUMMARY_PROMPT = """
You are an expert educator. Based on the topic "{topic}", generate a quick summary (2-3 paragraphs) that covers the core concepts, key definitions, and essential takeaways.
"""

DETAILED_NOTES_PROMPT = """
You are an expert educator. Based on the topic "{topic}", generate detailed revision notes.
Include:
1.  **Key Concepts:** Bullet points outlining the main ideas.
2.  **Definitions:** Clear definitions for important terms.
3.  **Examples:** Relevant examples to illustrate concepts.
4.  **Formulas/Equations:** Any critical formulas or equations (if applicable, use LaTeX for mathematical notation).
5.  **Important Theories/Models:** Brief explanations of major theories or models.
6.  **Potential Pitfalls/Common Mistakes:** Warnings about common misunderstandings.
"""

async def generate_revision_notes(topic, view_mode): # Changed to async def
    """
    Generates revision notes for a given topic and view mode (Quick Summary or Detailed Notes).
    """
    prompt_template = ""
    if view_mode == "Quick Summary":
        prompt_template = QUICK_SUMMARY_PROMPT
    else: # Detailed Notes
        prompt_template = DETAILED_NOTES_PROMPT

    prompt = PromptTemplate(template=prompt_template, input_variables=["topic"])

    try:
        # Use the shared async client and await the response
        response = await groq_async_client.chat.completions.create( # Added await
            model="llama3-8b-8192", # Or your preferred Groq model
            messages=[
                {"role": "system", "content": prompt.template},
                {"role": "user", "content": f"Topic: {topic}"}
            ],
            temperature=0.7,
            max_tokens=2048 if view_mode == "Detailed Notes" else 512, # Adjust token limits
        )
        return response.choices[0].message.content
    except APIStatusError as e:
        print(f"Groq API Error generating revision notes: {e.message} (Code: {e.code})")
        return f"Failed to generate revision notes due to API error: {e.message}"
    except Exception as e:
        print(f"Unexpected error generating revision notes: {e}")
        return f"Failed to generate revision notes due to an unexpected error: {e}"
