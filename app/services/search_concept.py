import asyncio
from groq import APIStatusError, RateLimitError
from .groq_client import client as groq_async_client

async def search_concept(query, retries=3, delay=2):
    """Searches for information on a given query and returns a detailed explanation."""
    if not query:
        return "No query provided."

    prompt = (
        f"Provide a clear and detailed explanation of the concept '{query}'. "
        f"Structure the response with an introduction, key points, and a conclusion. "
        f"Ensure the explanation is suitable for a learner seeking to understand the topic."
    )

    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable assistant providing clear explanations of concepts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return "Failed to retrieve information due to API rate limit."
        except APIStatusError as e:
            return f"Failed to retrieve information due to API error: {e.message}"
        except Exception as e:
            return f"Failed to retrieve information due to an unexpected error: {e}"