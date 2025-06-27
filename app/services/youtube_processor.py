# app/services/youtube_processor.py

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import asyncio
from groq import APIStatusError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .groq_client import client as groq_async_client # Correctly import the async client

def fetch_transcript(youtube_url, streamlit_ref=None):
    """
    Fetches the transcript for a given YouTube URL.
    This function is SYNCHRONOUS.
    """
    try:
        video_id = youtube_url.split("v=")[1].split("&")[0]
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'en-US']).fetch() # Try English, then US English
        
        full_transcript_text = " ".join([entry['text'] for entry in transcript])
        return full_transcript_text
    except NoTranscriptFound:
        if streamlit_ref:
            streamlit_ref.error("No transcript found for this video. It might not have captions or be a very new video.")
        print("Error: No transcript found for this video.")
        return None
    except TranscriptsDisabled:
        if streamlit_ref:
            streamlit_ref.error("Transcripts are disabled for this video.")
        print("Error: Transcripts are disabled for this video.")
        return None
    except Exception as e:
        if streamlit_ref:
            streamlit_ref.error(f"An unexpected error occurred while fetching transcript: {e}")
        print(f"Error fetching YouTube transcript: {e}")
        return None

async def _summarize_transcript_chunk_async(chunk, streamlit_ref=None, chunk_num=0, total_chunks=0):
    """Helper function to summarize a single transcript chunk asynchronously."""
    try:
        if streamlit_ref:
            streamlit_ref.info(f"Summarizing transcript chunk {chunk_num}/{total_chunks}...")
        print(f"Summarizing transcript chunk {chunk_num}/{total_chunks}...")

        response = await groq_async_client.chat.completions.create( # AWAIT IS CRUCIAL HERE
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Summarize the following YouTube transcript text concisely. Focus on key ideas and main points. Do not include timestamps or speaker names."},
                {"role": "user", "content": chunk}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except APIStatusError as e:
        if streamlit_ref:
            streamlit_ref.error(f"Groq API Error for transcript chunk {chunk_num}: {e.message} (Code: {e.code})")
        print(f"Groq API Error for transcript chunk {chunk_num}: {e.message} (Code: {e.code})")
        return None
    except Exception as e:
        if streamlit_ref:
            streamlit_ref.error(f"Unexpected error summarizing transcript chunk {chunk_num}: {e}")
        print(f"Unexpected error summarizing transcript chunk {chunk_num}: {e}")
        return None

async def summarize_transcript_async(transcript_text, streamlit_ref=None):
    """
    Summarizes large YouTube transcripts by chunking them and then combining summaries, asynchronously.
    """
    if not transcript_text:
        return "No transcript text provided to summarize."

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=12000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(transcript_text)

    if not chunks:
        return "No meaningful chunks could be created from the transcript."

    tasks = []
    for i, chunk in enumerate(chunks):
        tasks.append(_summarize_transcript_chunk_async(chunk, streamlit_ref, i + 1, len(chunks)))

    if streamlit_ref:
        streamlit_ref.info(f"Processing {len(chunks)} transcript chunks...")
    print(f"Processing {len(chunks)} transcript chunks...")

    chunk_summaries = await asyncio.gather(*tasks)

    chunk_summaries = [s for s in chunk_summaries if s is not None]

    if not chunk_summaries:
        return "Could not generate any summaries for the provided transcript chunks due to errors."

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries_text = "\n\n".join(chunk_summaries)

    if streamlit_ref:
        streamlit_ref.info("Combining and finalising transcript summary...")
    print("Combining and finalising transcript summary...")

    try:
        final_summary_response = await groq_async_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Combine the following individual summaries of a YouTube transcript into a comprehensive and cohesive final summary of the original video. Ensure no information is lost from the sub-summaries."},
                {"role": "user", "content": combined_summaries_text}
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        return final_summary_response.choices[0].message.content
    except APIStatusError as e:
        if streamlit_ref:
            streamlit_ref.error(f"Groq API Error combining transcript summaries: {e.message} (Code: {e.code})")
        print(f"Groq API Error combining transcript summaries: {e.message} (Code: {e.code})")
        return combined_summaries_text + f"\n\n(Note: Final transcript summary combination failed due to API error: {e.message})"
    except Exception as e:
        if streamlit_ref:
            streamlit_ref.error(f"Unexpected error combining transcript summaries: {e}")
        print(f"Unexpected error combining transcript summaries: {e}")
        return combined_summaries_text + "\n\n(Note: Final transcript summary combination failed due to an unexpected error.)"
