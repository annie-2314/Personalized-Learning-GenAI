# In app/services/youtube_processor.py

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from .groq_client import client

# NO 'import streamlit as st' HERE!

def get_video_id(url):
    import re
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_transcript(video_url, streamlit_ref=None): 
    video_id = get_video_id(video_url)
    if not video_id:
        print(f"Error: Could not extract video ID from URL: {video_url}")
        if streamlit_ref: 
            streamlit_ref.error("Could not extract video ID from the provided URL.") 
        return None

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry['text'] for entry in transcript_list])
        return text
    except NoTranscriptFound:
        msg = f"No transcript found for video ID: {video_id} (URL: {video_url}). The video might not have captions."
        print(msg)
        if streamlit_ref: # <--- ADDED CHECK
            streamlit_ref.warning(msg) # <--- MODIFIED LINE
        return None
    except TranscriptsDisabled:
        msg = f"Transcripts are disabled for video ID: {video_id} (URL: {video_url})."
        print(msg)
        if streamlit_ref: # <--- ADDED CHECK
            streamlit_ref.warning(msg) # <--- MODIFIED LINE
        return None
    except Exception as e:
        msg = f"An unexpected error occurred while fetching transcript for video ID: {video_id} (URL: {video_url}). Error: {e}"
        print(msg)
        if streamlit_ref: # <--- ADDED CHECK
            streamlit_ref.error(f"An error occurred while fetching transcript: {e}. Please check the video link.") # <--- MODIFIED LINE
        return None

def summarize_transcript(transcript_text, streamlit_ref=None): # <--- MODIFIED LINE
    if not transcript_text:
        return "No transcript available to summarize."

    from langchain_text_splitters import RecursiveCharacterTextSplitter # <--- Moved import here if not global

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=12000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(transcript_text)
    chunk_summaries = []

    for i, chunk in enumerate(chunks):
        if streamlit_ref: # <--- ADDED CHECK
            streamlit_ref.info(f"Summarizing transcript chunk {i+1}/{len(chunks)}...") # <--- MODIFIED LINE
        print(f"Summarizing transcript chunk {i+1}/{len(chunks)}...")

        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Summarize the following transcript chunk concisely."},
                    {"role": "user", "content": chunk}
                ]
            )
            chunk_summaries.append(response.choices[0].message.content)
        except Exception as e:
            if streamlit_ref: # <--- ADDED CHECK
                streamlit_ref.error(f"Error summarizing transcript chunk {i+1}: {e}") # <--- MODIFIED LINE
            print(f"Error summarizing transcript chunk {i+1}: {e}")
            continue

    if not chunk_summaries:
        return "Could not generate summary for the provided transcript."

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries_text = "\n\n".join(chunk_summaries)

    if streamlit_ref: # <--- ADDED CHECK
        streamlit_ref.info("Combining and finalising transcript summary...") # <--- MODIFIED LINE
    print("Combining and finalising transcript summary...")

    try:
        final_summary_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original YouTube transcript."},
                {"role": "user", "content": combined_summaries_text}
            ]
        )
        return final_summary_response.choices[0].message.content
    except Exception as e:
        if streamlit_ref: # <--- ADDED CHECK
            streamlit_ref.error(f"Error combining transcript summaries: {e}") # <--- MODIFIED LINE
        print(f"Error combining transcript summaries: {e}")
        return combined_summaries_text + "\n\n(Note: Final transcript summary combination failed due to API limits or other error.)"
