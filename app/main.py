import base64
import streamlit as st
from datetime import datetime
from services import pdf_processor, youtube_processor, quiz_generator
from services.revision_notes import generate_revision_notes
from fpdf import FPDF
from utils import database
from services.search_concept import search_concept
from services.spaced_repetition import get_review_schedule, mark_reviewed


# Initialize database
database.initialize_db()

st.set_page_config(page_title="Personalized Learning Coach", layout="wide")
def set_bg_from_local(image_file):
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

# Call with correct path
set_bg_from_local("app/bg2.png")
# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Upload Content", "Quiz Me", "Revision Notes", "Spaced Repetition Planner", "Search & Explore"])

# Shared user greeting
st.sidebar.markdown("---")
st.sidebar.markdown("*User:* Annie Siri")
st.sidebar.markdown("*Date:* " + datetime.today().strftime('%Y-%m-%d'))


# Page: Dashboard
if page == "Dashboard":
    st.title("📊 Learning Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Topics Learned", "12")
    col2.metric("Memory Retention", "72%")
    col3.metric("Pending Reviews", "4")

    st.subheader("Next Recommended Action")
    st.info("Revise: Neural Networks - Medium Priority")

# Page: Upload Content
elif page == "Upload Content":
    st.title("📤 Upload Your Learning Material")
    upload_option = st.radio("Choose content type :", ["PDF", "YouTube Link", "Raw Text"])

    if upload_option == "PDF":
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded_pdf:
            text = pdf_processor.extract_text_from_pdf(uploaded_pdf)
            summary = pdf_processor.summarize_text(text)
            st.success("PDF summarized successfully.")
            st.write(summary)
    elif upload_option == "YouTube Link":
        yt_link = st.text_input("Paste YouTube Transcript Link:")
        if yt_link:
            transcript = youtube_processor.fetch_transcript(yt_link)
            summary = youtube_processor.summarize_transcript(transcript)
            st.success("Transcript summarized successfully.")
            st.write(summary)
    elif upload_option == "Raw Text":
        raw_text = st.text_area("Paste your notes here:")
        if raw_text:
            summary = pdf_processor.summarize_text(raw_text)
            st.success("Notes summarized successfully.")
            st.write(summary)

# Page: Quiz Me
elif page == "Quiz Me":
    st.title("🧠 Personalized Quiz")
    topic = st.text_input("Enter Topic")
    difficulty = st.radio("Select Difficulty", ["Easy", "Medium", "Hard"])
    quiz_type = st.selectbox("Quiz Type", ["MCQ", "Fill in the Blanks", "Short Answer"])

    if st.button("Start Quiz"):
        quiz = quiz_generator.generate_quiz(topic, difficulty, quiz_type)
        st.write(quiz)

# Page: Revision Notes


# Page: Revision Notes
elif page == "Revision Notes":
    st.title("📝 Revision Notes")
    
    # Get user input for topic
    selected_topic = st.text_input("Enter Topic")
    
    # Select view mode (Quick Summary or Detailed Notes)
    view_mode = st.radio("View Mode", ["Quick Summary", "Detailed Notes"])

    if st.button("Generate Notes"):
        # Generate revision notes using the service function
        revision_notes = generate_revision_notes(selected_topic, view_mode)
        
        # Display the generated notes
        st.write(revision_notes)

        # PDF generation for download
        def generate_pdf(notes, file_name="revision_notes.pdf"):
            pdf = FPDF()
            pdf.add_page()
            
            # Add title
            pdf.set_font("Arial", size=16)
            pdf.cell(200, 10, txt="Revision Notes", ln=True, align="C")

            # Add notes content
            pdf.ln(10)  # Add a line break
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, txt=notes)  # Allows multiline text

            # Output the file
            pdf.output(file_name)

        # Allow user to download the generated notes as a PDF
        generate_pdf(revision_notes)
        with open("revision_notes.pdf", "rb") as pdf_file:
            st.download_button(
                label="Download PDF",
                data=pdf_file,
                file_name="revision_notes.pdf",
                mime="application/pdf"
            )


# Page: Spaced Repetition Planner
elif page == "Spaced Repetition Planner":
    st.title("⏳ Spaced Repetition Planner")

    user_name = "Annie Siri"  # Could be dynamic
    schedule = get_review_schedule(user_name)

    st.subheader("Your Memory Review Schedule")

    for label in ["Today", "Tomorrow", "Later"]:
        if schedule[label]:
            st.markdown(f"**{label}:**")
            for topic in schedule[label]:
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"- {topic}")
                if label == "Today" and col2.button(f"✅ Mark Reviewed", key=topic):
                    mark_reviewed(user_name, topic)
                    st.success(f"Marked '{topic}' as reviewed.")
                    st.experimental_rerun()
        else:
            st.markdown(f"**{label}:** *(No topics)*")


# Page: Search & Explore
elif page == "Search & Explore":
    st.title("🔍 Explore Past Material")
    query = st.text_input("Ask something or search a concept:")

    if query:
        # Perform semantic search using Groq (implemented in the backend)
        search_results = search_concept(query)
        if search_results:
            st.success(f"Top results for: {query}")
            for result in search_results:
                st.markdown(f"- {result}")
        else:
            st.warning("No relevant results found.")



