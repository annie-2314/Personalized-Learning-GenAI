from .groq_client import client
import json

def generate_quiz(topic, difficulty, quiz_type):
    prompt = f"""
    You are a quiz generator. Generate a {difficulty} {quiz_type} quiz on the topic: {topic}.
    Return the quiz in JSON format as a list of exactly 5 questions. Each question must have:
    - "question": The question text (string, phrased as a fill-in-the-blank for 'Fill in the Blanks', a short question for 'Short Answer', or a multiple-choice question for 'MCQ').
    - "options": A list of exactly 4 answer options (strings) for 'MCQ', or an empty list [] for 'Fill in the Blanks' and 'Short Answer'.
    - "correct_answer": The correct answer (string, one of the options for 'MCQ', or a single word/short phrase for 'Fill in the Blanks' and 'Short Answer').
    - "type": The quiz type ("MCQ", "Fill in the Blanks", or "Short Answer").
    For 'Fill in the Blanks', use incomplete sentences with a blank (e.g., "The keyword to define a function in Python is ____.").
    For 'Short Answer', use questions requiring a brief response (e.g., "What is the purpose of the print function in Python?").
    For 'MCQ', provide 4 distinct options with one correct answer.
    Ensure the response is valid JSON, enclosed in square brackets, with no extra text before or after the JSON.
    Example for MCQ:
    [
        {{
            "question": "What is Python?",
            "options": ["A snake", "A programming language", "A database", "A framework"],
            "correct_answer": "A programming language",
            "type": "MCQ"
        }}
    ]
    Example for Fill in the Blanks:
    [
        {{
            "question": "The keyword to define a function in Python is ____.",
            "options": [],
            "correct_answer": "def",
            "type": "Fill in the Blanks"
        }}
    ]
    Example for Short Answer:
    [
        {{
            "question": "What is the purpose of the print function in Python?",
            "options": [],
            "correct_answer": "To output text",
            "type": "Short Answer"
        }}
    ]
    Generate exactly 5 questions for {quiz_type} on {topic}.
    """
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Generate quiz questions in valid JSON format with no extra text before or after."},
                {"role": "user", "content": prompt}
            ]
        )
        quiz_content = response.choices[0].message.content.strip()
        print("DEBUG: quiz_generator raw response:", quiz_content)
        
        try:
            quiz_data = json.loads(quiz_content)
            print("DEBUG: quiz_generator parsed output:", quiz_data)
            if isinstance(quiz_data, list) and len(quiz_data) == 5 and all(isinstance(q, dict) and q.get("question") and q.get("correct_answer") and q.get("type") == quiz_type for q in quiz_data):
                for question in quiz_data:
                    if quiz_type in ["Fill in the Blanks", "Short Answer"]:
                        question["options"] = []
                    elif quiz_type == "MCQ":
                        if not (isinstance(question.get("options", []), list) and len(question.get("options", [])) == 4):
                            question["options"] = ["Option 1", "Option 2", "Option 3", "Option 4"]
                            question["correct_answer"] = "Option 1"
                    question["type"] = quiz_type
                return quiz_data
            else:
                print("DEBUG: Invalid quiz format or wrong number of questions")
        except json.JSONDecodeError as e:
            print(f"Error parsing quiz JSON: {e}")
        # Fallback: 5 default questions
        fallback_questions = [
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
        return fallback_questions
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return []