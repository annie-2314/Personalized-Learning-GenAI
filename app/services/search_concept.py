from .groq_client import client

def search_concept(query):
    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "Provide a single, continuous paragraph explanation without bullet points, lists, numbering, or special characters that could be split into individual characters. Ensure the response is plain text suitable for direct display."},
                {"role": "user", "content": f"Find relevant explanations or concepts for: {query}"}
            ]
        )
        search_results = response.choices[0].message.content.strip().replace('\n', ' ').replace('\r', ' ')
        print("DEBUG: search_concept output type:", type(search_results))
        print("DEBUG: search_concept output:", repr(search_results))
        return search_results
    except Exception as e:
        print(f"Error performing semantic search: {e}")
        return ""