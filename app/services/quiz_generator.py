import asyncio
import json
from groq import APIStatusError, RateLimitError
from .groq_client import client as groq_async_client

async def generate_quiz(topic, difficulty, quiz_type, retries=3, delay=2):
    """Generates a quiz with 5 questions for the given topic, difficulty, and type."""
    if not topic:
        return []

    question_types = {
        "MCQ": "multiple-choice questions with 4 options each, including one correct answer",
        "Fill in the Blanks": "fill-in-the-blank questions with a single correct answer",
        "Short Answer": "short-answer questions with a concise correct answer"
    }
    prompt = (
        f"Generate exactly 5 {question_types.get(quiz_type, 'multiple-choice questions')} "
        f"for the topic '{topic}' at a {difficulty.lower()} difficulty level. "
        f"Return the response as a JSON list of 5 objects, each containing: "
        f"'question' (the question text), 'options' (list of 4 strings for MCQ, empty list for others), "
        f"'correct_answer' (the correct answer as a string), and 'type' (the quiz type). "
        f"Ensure valid JSON with no extra text before or after."
    )

    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Generate quiz questions in valid JSON format with no extra text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            quiz_content = response.choices[0].message.content.strip()
            try:
                quiz_data = json.loads(quiz_content)
                if isinstance(quiz_data, list) and len(quiz_data) == 5 and all(
                    isinstance(q, dict) and q.get("question") and q.get("correct_answer") and q.get("type") == quiz_type
                    for q in quiz_data
                ):
                    for question in quiz_data:
                        if quiz_type in ["Fill in the Blanks", "Short Answer"]:
                            question["options"] = []
                        elif quiz_type == "MCQ" and not (
                            isinstance(question.get("options", []), list) and len(question.get("options", [])) == 4
                        ):
                            question["options"] = ["Option 1", "Option 2", "Option 3", "Option 4"]
                            question["correct_answer"] = "Option 1"
                        question["type"] = quiz_type
                    return quiz_data
            except json.JSONDecodeError:
                pass
            # Fallback: 5 default questions
            return [
                {
                    "question": f"The keyword to define a function in {topic} is ____." if quiz_type == "Fill in the Blanks" else f"What is the purpose of the print function in {topic}?" if quiz_type == "Short Answer" else f"What is {topic}?",
                    "options": [] if quiz_type in ["Fill in the Blanks", "Short Answer"] else ["A programming language", "A database", "A framework", "A snake"],
                    "correct_answer": "def" if quiz_type == "Fill in the Blanks" else "To output text" if quiz_type == "Short Answer" else "A programming language",
                    "type": quiz_type
                },
                {
                    "question": f"The syntax to define a list in {topic} is ____." if quiz_type == "Fill in the Blanks" else f"What is the syntax to define a list in {topic}?" if quiz_type == "Short Answer" else f"What is the syntax to define a list in {topic}?",
                    "options": [] if quiz_type in ["Fill in the Blanks", "Short Answer"] else ["Using parentheses ()", "Using square brackets []", "Using curly brackets {}", "Using angle brackets <>"],
                    "correct_answer": "[]" if quiz_type == "Fill in the Blanks" else "Using square brackets []" if quiz_type == "Short Answer" else "Using square brackets []",
                    "type": quiz_type
                },
                {
                    "question": f"The purpose of indentation in {topic} is to ____." if quiz_type == "Fill in the Blanks" else f"What is the purpose of indentation in {topic}?" if quiz_type == "Short Answer" else f"What is the purpose of indentation in {topic}?",
                    "options": [] if quiz_type in ["Fill in the Blanks", "Short Answer"] else ["To denote a comment", "To define a variable", "To specify a block of code", "To indicate a loop"],
                    "correct_answer": "specify a block of code" if quiz_type == "Fill in the Blanks" else "To specify a block of code" if quiz_type == "Short Answer" else "To specify a block of code",
                    "type": quiz_type
                },
                {
                    "question": f"The keyword to import a module in {topic} is ____." if quiz_type == "Fill in the Blanks" else f"What is the keyword to import a module in {topic}?" if quiz_type == "Short Answer" else f"What is the keyword to import a module in {topic}?",
                    "options": [] if quiz_type in ["Fill in the Blanks", "Short Answer"] else ["import", "include", "require", "load"],
                    "correct_answer": "import",
                    "type": quiz_type
                },
                {
                    "question": f"The symbol to comment out a line in {topic} is ____." if quiz_type == "Fill in the Blanks" else f"How do you comment out a line in {topic}?" if quiz_type == "Short Answer" else f"How do you comment out a line in {topic}?",
                    "options": [] if quiz_type in ["Fill in the Blanks", "Short Answer"] else ["#", "//", "/*", "--"],
                    "correct_answer": "#" if quiz_type == "Fill in the Blanks" else "Using #" if quiz_type == "Short Answer" else "Using #",
                    "type": quiz_type
                }
            ]
        except RateLimitError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))
                continue
            return []
        except APIStatusError:
            return []
        except Exception:
            return []
