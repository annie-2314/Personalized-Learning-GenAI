import asyncio
from groq import APIStatusError, RateLimitError
from .groq_client import client as groq_async_client

async def generate_revision_notes(topic, view_mode, retries=3, delay=2):
    """Generates revision notes for a given topic in the specified view mode."""
    if not topic:
        return "No topic provided to generate revision notes."

    prompt = (
        f"Generate {'concise summary notes' if view_mode == 'Quick Summary' else 'detailed revision notes'} "
        f"for the topic '{topic}'. Ensure the notes are clear, structured, and suitable for studying."
    )

    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a study assistant creating revision notes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048 if view_mode == "Detailed Notes" else 1024,
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return f"Could not generate revision notes for '{topic}' due to API rate limit."
        except APIStatusError as e:
            return f"Could not generate revision notes for '{topic}' due to API error: {e.message}"
        except Exception as e:
            return f"Could not generate revision notes for '{topic}' due to an unexpected error: {e}"