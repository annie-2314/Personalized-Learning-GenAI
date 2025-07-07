import asyncio
import json
import logging
from groq import APIStatusError, RateLimitError
from .groq_client import client as groq_async_client

logging.basicConfig(level=logging.INFO, filename='app_logs.log')

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
        f"Generate EXACTLY 5 {question_types.get(quiz_type, 'multiple-choice questions')} "
        f"for the topic '{topic}' at a {difficulty.lower()} difficulty level. "
        f"Output ONLY a valid JSON list of 5 objects, each with: "
        f"'question' (string), 'options' (list of 4 strings for MCQ, empty list otherwise), "
        f"'correct_answer' (string), and 'type' (string matching '{quiz_type}'). "
        f"DO NOT include any text outside the JSON array, ensure proper JSON syntax."
    )

    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Generate ONLY valid JSON for quiz questions with no extra text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Lowered for more consistent output
                max_tokens=2048,
            )
            quiz_content = response.choices[0].message.content.strip()
            try:
                quiz_data = json.loads(quiz_content)
                if (isinstance(quiz_data, list) and len(quiz_data) == 5 and all(
                    isinstance(q, dict) and q.get("question") and q.get("correct_answer") and q.get("type") == quiz_type
                    for q in quiz_data
                )):
                    for question in quiz_data:
                        if quiz_type in ["Fill in the Blanks", "Short Answer"]:
                            question["options"] = []
                        elif quiz_type == "MCQ" and not (isinstance(question.get("options", []), list) and len(question.get("options", [])) == 4):
                            logging.warning(f"Invalid options for question in {topic}, setting defaults")
                            question["options"] = ["Option A", "Option B", "Option C", "Option D"]
                            question["correct_answer"] = "Option A"  # Should be derived from AI if possible
                        question["type"] = quiz_type
                    logging.info(f"Successfully generated quiz for {topic}")
                    return quiz_data
            except json.JSONDecodeError:
                logging.warning(f"JSON decode failed for {topic} on attempt {attempt + 1}/{retries}: {quiz_content}")
                if attempt == retries - 1:
                    logging.error(f"Failed to parse quiz JSON after {retries} attempts for {topic}")
                    return []  # Return empty only after all retries
                continue
        except RateLimitError:
            logging.warning(f"Rate limit hit for {topic} on attempt {attempt + 1}/{retries}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))
                continue
            logging.error(f"Rate limit exceeded after {retries} attempts for {topic}")
            return []
        except APIStatusError as e:
            logging.error(f"API error for {topic}: {e.message}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error for {topic}: {e}")
            return []

    return []  # Fallback if all retries fail