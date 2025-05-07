from services.groq_client import client

def generate_quiz(topic, difficulty, quiz_type):
    prompt = f"Create a {difficulty} {quiz_type} quiz on the topic: {topic}."
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": "Generate quiz questions."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
