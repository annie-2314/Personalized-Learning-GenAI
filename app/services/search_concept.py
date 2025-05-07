# from groq import client
from services.groq_client import client

def search_concept(query):
    # Use Groq's embeddings to perform a semantic search
    try:
        # Create a prompt with the query
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "Perform a semantic search."},
                {"role": "user", "content": f"Find relevant explanations or concepts for: {query}"}
            ]
        )
        # Extract results from the response
        search_results = response.choices[0].message.content.strip().split('\n')
        return search_results
    except Exception as e:
        print(f"Error performing semantic search: {e}")
        return []
