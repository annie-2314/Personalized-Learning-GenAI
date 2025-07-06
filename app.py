import asyncio
import io
import logging
import fitz
import sys
import os
import base64
import streamlit as st
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import pandas as pd
import sqlite3


# --- IMPORTANT IMPORTS ---
from app.services import pdf_processor, youtube_processor, quiz_generator
from app.services.revision_notes import generate_revision_notes
from app.services.search_concept import search_concept
from app.utils import database as db_utils

# --- Global/Session State Initialization ---
db_utils.initialize_db()

if 'user_name' not in st.session_state:
    st.session_state.user_name = "Annie Siri"

st.set_page_config(page_title="Personalized Learning Coach", page_icon="📚", layout="wide")

# Background setup
def set_bg_from_local(image_file):
    try:
        with open(image_file, "rb") as image:
            encoded = base64.b64encode(image.read()).decode()
            st.markdown(
                f"""
                <style>
                [data-testid="stAppViewContainer"] {{
                    background-image: url("data:image/png;base64,{encoded}");
                    background-size: cover;
                    background-position: center;
                    background-attachment: fixed;
                }}
                [data-testid="stSidebar"] {{
                    background-color: rgba(255, 255, 255, 0.6);
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
    except FileNotFoundError:
        st.warning("Background image not found. Using default background.")

set_bg_from_local("app/bg2.png")

# Check if username exists
def username_exists(username):
    try:
        conn = sqlite3.connect("data/database.db", check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT user_name FROM streaks WHERE user_name = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"DEBUG: Error checking username: {e}")
        return False

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Create Account", "Dashboard", "Upload Content", "Quiz Me", "Revision Notes", "Spaced Repetition Planner", "Progress Tracker", "Search & Explore"])
st.sidebar.markdown("---")
user_name_input = st.sidebar.text_input("Username", value=st.session_state.user_name, key="sidebar_user")
if user_name_input:
    st.session_state.user_name = user_name_input
st.sidebar.markdown(f"*User:* {st.session_state.user_name}")
st.sidebar.markdown("*Date:* " + datetime.today().strftime('%Y-%m-%d'))

# Page: Create Account
if page == "Create Account":
    st.title("👤 Create Account")
    new_username = st.text_input("Enter a new username", key="new_username")
    if st.button("Create Account"):
        if new_username:
            if not username_exists(new_username):
                st.session_state.user_name = new_username
                db_utils.add_topic(new_username, "welcome")  # Add a dummy topic to initialize user
                st.success(f"Account created for '{new_username}'! You can now use the app.")
                st.info("Navigate to other pages using the sidebar.")
            else:
                st.error("Username already exists. Please choose a different username.")
        else:
            st.warning("Please enter a username.")

# Page: Dashboard
elif page == "Dashboard":
    st.title("📊 Learning Dashboard")
    try:
        schedule = db_utils.get_review_schedule(st.session_state.user_name)
        topics = db_utils.get_all_topics(st.session_state.user_name)
        pending_reviews = len(schedule["Today"])
        total_topics = len(topics)
        avg_memory = sum([topic[2] for topic in topics]) / max(total_topics, 1) if total_topics > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Topics Learned", total_topics)
        col2.metric("Avg. Memory Retention", f"{avg_memory:.1f}%")
        col3.metric("Pending Reviews", pending_reviews)

        st.subheader("Next Recommended Action")
        if pending_reviews > 0:
            st.info(f"Revise: {schedule['Today'][0]} - High Priority")
        else:
            st.info("No topics due for review today. Keep learning!")
    except Exception as e:
        st.error(f"Error loading dashboard: {e}. Check if data/database.db exists.")

# Page: Upload Content
elif page == "Upload Content":
    st.title("📤 Upload Your Learning Material")
    upload_option = st.radio("Choose content type:", ["PDF", "YouTube Link", "Raw Text"])

    if upload_option == "PDF":
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_pdf:
            text = pdf_processor.extract_text_from_pdf(uploaded_pdf)
            if text:
                try:
                    summary = asyncio.run(pdf_processor.summarize_text_async(text))
                    st.write(summary)  # Show only the summary
                    topic_name = st.text_input("Enter a brief topic name for review:", key="pdf_topic_input")
                    if st.button("Add to Review List", key="add_pdf_topic_button"):
                        if topic_name:
                            db_utils.add_topic(st.session_state.user_name, topic_name)
                            st.success(f"'{topic_name}' added to your review schedule with memory level 100!")
                        else:
                            st.warning("Please enter a topic name.")
                except Exception as e:
                    st.error(f"Failed to summarize PDF: {e}")
            else:
                st.error("No text extracted from PDF. Please upload a valid PDF.")

    elif upload_option == "YouTube Link":
        youtube_url = st.text_input("Enter YouTube URL:")
        if youtube_url:
            video_id = youtube_processor.extract_video_id(youtube_url)
            if video_id:
                transcript, error = asyncio.run(youtube_processor.get_transcript(youtube_url))
                if transcript:
                    try:
                        summary = asyncio.run(youtube_processor.summarize_transcript(transcript))
                        st.write(summary)
                        topic_name = st.text_input("Enter a brief topic name for review:", key="youtube_topic_input")
                        if st.button("Add to Review List", key="add_youtube_topic_button"):
                            if topic_name:
                                db_utils.add_topic(st.session_state.user_name, topic_name)
                                st.success(f"'{topic_name}' added to your review schedule with memory level 100!")
                            else:
                                st.warning("Please enter a topic name.")
                    except Exception as e:
                        st.error(f"Failed to summarize YouTube transcript: {e}")
                        logging.error(f"Summarization failed for video ID {video_id}: {str(e)}")
                else:
                    st.error(error or "Unable to fetch transcript for this video. Try another video or paste notes in the Raw Text section below.")
                    st.markdown("[Search for videos with transcripts enabled](https://www.youtube.com/results?search_query=educational+lecture)")
                    if error:
                        logging.warning(f"Transcript fetch failed for video ID {video_id}: {error}")
            else:
                st.error("Invalid YouTube URL. Please use a format like https://youtu.be/VIDEO_ID.")

    elif upload_option == "Raw Text":
        raw_text = st.text_area("Paste your notes here:")
        if raw_text:
            try:
                summary = asyncio.run(pdf_processor.summarize_text_async(raw_text))
                st.write(summary)
                topic_name = st.text_input("Enter a brief topic name for review:", key="raw_text_topic_input")
                if st.button("Add to Review List", key="add_raw_text_topic_button"):
                    if topic_name:
                        db_utils.add_topic(st.session_state.user_name, topic_name)
                        st.success(f"'{topic_name}' added to your review schedule with memory level 100!")
                    else:
                        st.warning("Please enter a topic name.")
            except Exception as e:
                st.error(f"Failed to summarize text: {e}")
# Page: Quiz Me
elif page == "Quiz Me":
    st.title("🧠 Personalized Quiz")
    topic = st.text_input("Enter Topic", key="quiz_topic")
    difficulty = st.radio("Select Difficulty", ["Easy", "Medium", "Hard"])
    quiz_type = st.selectbox("Quiz Type", ["MCQ", "Fill in the Blanks", "Short Answer"])

    if st.button("Start Quiz"):
        if topic:
            # quiz = quiz_generator.generate_quiz(topic, difficulty, quiz_type)
            quiz = asyncio.run(quiz_generator.generate_quiz(topic, difficulty, quiz_type))

            if quiz and isinstance(quiz, list) and len(quiz) == 5:
                st.session_state.quiz = quiz
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                db_utils.add_topic(st.session_state.user_name, topic)  # Add topic to database
                st.success("Quiz generated successfully!")
            else:
                st.error("Failed to generate 5 questions. Please try again.")
                print(f"DEBUG: Quiz generation failed for topic '{topic}', type '{quiz_type}', difficulty '{difficulty}'")
        else:
            st.warning("Please enter a topic.")

    if "quiz" in st.session_state and st.session_state.quiz and not st.session_state.quiz_submitted:
        st.subheader(f"{quiz_type} Quiz on {topic} ({difficulty})")
        with st.form("quiz_form"):
            for i, question in enumerate(st.session_state.quiz):
                st.write(f"**Question {i+1}:** {question['question']}")
                options = question.get("options", [])
                if quiz_type == "MCQ" and isinstance(options, list) and len(options) == 4:
                    answer = st.radio(
                        f"Select an answer for question {i+1}",
                        options,
                        key=f"q_{i}"
                    )
                    st.session_state.user_answers[i] = answer
                else:  # Fill in the Blanks or Short Answer, or invalid MCQ
                    if quiz_type == "MCQ":
                        st.warning(f"Question {i+1} has invalid options for MCQ. Using text input.")
                        print(f"DEBUG: Invalid MCQ options for question {i+1}: {options}")
                    answer = st.text_input(
                        f"Your answer for question {i+1}",
                        key=f"q_{i}",
                        value=""
                    )
                    st.session_state.user_answers[i] = answer.strip() if answer else ""
            submit_button = st.form_submit_button("Submit Quiz")

        if submit_button:
            score = 0
            total = len(st.session_state.quiz)
            st.subheader("Quiz Results")
            for i, question in enumerate(st.session_state.quiz):
                user_answer = st.session_state.user_answers.get(i, "")
                correct_answer = str(question.get("correct_answer", "Unknown"))
                is_correct = user_answer.lower() == correct_answer.lower() if user_answer and correct_answer != "Unknown" else False
                if is_correct:
                    score += 1
                st.write(f"**Question {i+1}:** {question['question']}")
                st.write(f"Your answer: {user_answer}")
                st.write(f"Correct answer: {correct_answer}")
                st.write("✅ Correct" if is_correct else "❌ Incorrect")
            percentage = (score / total) * 100
            st.write(f"**Your Score: {score}/{total} ({percentage:.1f}%)**")
            if score >= 3:  # Mark as reviewed if score ≥60%
                db_utils.mark_reviewed(st.session_state.user_name, topic)
            st.session_state.quiz_submitted = True
    elif st.session_state.get("quiz_submitted", False):
        st.info("Quiz submitted! Start a new quiz to continue.")
# Page: Revision Notes
elif page == "Revision Notes":
    import inspect
    st.title("📝 Revision Notes")
    selected_topic = st.text_input("Enter Topic")
    view_mode = st.radio("View Mode", ["Quick Summary", "Detailed Notes"])

    if st.button("Generate Notes"):
        if not selected_topic:
            st.warning("Please enter a topic.")
            st.stop()

        try:
            # ✅ RUN the coroutine properly
            result = generate_revision_notes(selected_topic, view_mode)
            if inspect.iscoroutine(result):
                notes = asyncio.run(result)
            else:
                notes = result

            # ✅ Check if notes is a valid string
            if not isinstance(notes, str):
                st.error("Generated notes are not in string format.")
                st.stop()

            # ✅ Display on screen
            st.success("Notes generated successfully!")
            st.write(notes)

            # ✅ Generate downloadable PDF
            from fpdf import FPDF

            def generate_pdf(content, filename="revision_notes.pdf"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=16)
                pdf.cell(200, 10, txt="Revision Notes", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=content)
                pdf.output(filename)

            generate_pdf(notes)
            with open("revision_notes.pdf", "rb") as pdf_file:
                st.download_button(
                    label="Download PDF",
                    data=pdf_file,
                    file_name="revision_notes.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"❌ Error: {e}")


# Page: Spaced Repetition Planner
elif page == "Spaced Repetition Planner":
    st.title("⏳ Spaced Repetition Planner")
    try:
        streak = db_utils.get_streak(st.session_state.user_name)
        st.write(f"**Current Streak:** {streak} day{'s' if streak != 1 else ''}")
        schedule = db_utils.get_review_schedule(st.session_state.user_name)
        st.subheader("Your Memory Review Schedule")
        for period in ["Today", "Tomorrow", "Later"]:
            st.write(f"**{period}:**")
            topics = schedule.get(period, [])
            if topics:
                for topic in topics:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"- {topic}")
                    with col2:
                        if st.button(f"Review {topic}", key=f"review_{period}_{topic}_{st.session_state.user_name}"):
                            db_utils.mark_reviewed(st.session_state.user_name, topic)
                            st.success(f"Marked '{topic}' as reviewed! Memory level updated.")
                            st.rerun()  # Refresh to update schedule
            else:
                st.write("No topics scheduled for this period.")
    except Exception as e:
        st.error(f"Error loading schedule: {e}. Please ensure data/database.db exists and is accessible.")

# Page: Progress Tracker
elif page == "Progress Tracker":
    st.title("📈 Progress Tracker")
    topics = db_utils.get_all_topics(st.session_state.user_name)
    if topics:
        # Prepare data for charts
        df = pd.DataFrame(topics, columns=["user_name", "topic_name", "memory_level", "last_reviewed", "next_review"])
        df["last_reviewed"] = pd.to_datetime(df["last_reviewed"])
        
        # Line chart: Topics learned over time
        df["date"] = df["last_reviewed"].dt.date
        topic_counts = df.groupby("date").size().reset_index(name="count")
        fig1 = px.line(topic_counts, x="date", y="count", title="Topics Learned Over Time")
        st.plotly_chart(fig1)

        # Bar chart: Memory retention distribution
        memory_bins = pd.cut(df["memory_level"], bins=[0, 25, 50, 75, 100], labels=["0-25%", "26-50%", "51-75%", "76-100%"])
        memory_dist = memory_bins.value_counts().sort_index()
        fig2 = px.bar(x=memory_dist.index, y=memory_dist.values, title="Memory Retention Distribution", labels={"x": "Memory Level", "y": "Number of Topics"})
        st.plotly_chart(fig2)
    else:
        st.info("No topics available to display progress. Start learning to see your progress!")

# Page: Search & Explore
elif page == "Search & Explore":
    st.title("🔍 Explore Past Material")
    query = st.text_input("Ask something or search a concept:")
    if query:
        try:
            search_results = asyncio.run(search_concept(query))
            if isinstance(search_results, str) and search_results.strip():
                st.success(f"Top results for: {query}")
                st.write(search_results)
            else:
                st.warning(f"No relevant results found or invalid output: {search_results}")
        except Exception as e:
            st.error(f"Failed to retrieve information: {e}")


