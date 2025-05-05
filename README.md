# 📚 Personal Learning Assistant GenAI

An AI-powered interactive learning assistant that helps students learn smarter by summarizing content, generating adaptive quizzes, and planning revisions using memory-based spaced repetition.
## 📹 Demo Video
[Download Video](app/demo video.mp4)


## 🚀 Features

🔹 **Content Upload**
- Upload **PDFs**, **YouTube transcripts**, or **raw text notes**
- Automatically extract and summarize core concepts using LLMs

🔹 **Quiz Generator**
- Personalized quizzes based on uploaded content
- Supports **MCQs**, **Fill-in-the-Blanks**, and **Short Answer** types
- Difficulty levels: *Easy*, *Medium*, *Hard*

🔹 **Revision Notes**
- Generate **quick summaries** or **detailed notes** on any topic
- Option to **download notes as PDF**

🔹 **Spaced Repetition Planner**
- AI schedules your topic reviews based on memory retention
- Encourages long-term learning and recall

🔹 **Semantic Search**
- Search previously learned concepts using intelligent embeddings
- Returns conceptually similar matches even if wording is different

---

## 🧠 Tech Stack

| Layer              | Tech Used                                   |
|-------------------|----------------------------------------------|
| Frontend          | [Streamlit](https://streamlit.io)            |
| Backend           | [FastAPI (planned for production)]           |
| GenAI             | Groq Cloud + LLaMA 4 Scout 17B Instruct Model |
| Summarization     | LLM-based text abstraction (via API)         |
| Quiz Generation   | Prompt-tuned LLM-based question synthesis     |
| Embeddings & Search | Vector store + semantic similarity search |
| Database          | SQLite (for topic tracking and review dates) |

---

## 🖼️ UI Highlights

- 📊 Dashboard with retention metrics  
- 📤 Upload and auto-summarize content  
- 🧠 Personalized quiz section  
- 📝 Revision note generator (PDF export)  
- 🔁 Spaced repetition scheduler  
- 🔍 Concept search using embeddings  



