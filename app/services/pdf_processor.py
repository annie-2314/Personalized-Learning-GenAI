# app/services/pdf_processor.py

import io
import fitz  # PyMuPDF <--- ADD THIS IMPORT
import asyncio
from groq import APIStatusError # <--- KEEP THIS IMPORT
from langchain_text_splitters import RecursiveCharacterTextSplitter # <--- KEEP THIS IMPORT
from .groq_client import client as groq_async_client # <--- KEEP THIS IMPORT (ensure client is AsyncGroq)


def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from an uploaded Streamlit PDF file object using PyMuPDF.
    """
    # PyMuPDF works directly with file-like objects or bytes
    file_stream = io.BytesIO(uploaded_file.getvalue())
    
    text = ""
    try:
        with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
            for page in doc:
                extracted_page_text = page.get_text()
                if extracted_page_text:
                    text += extracted_page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        # In a Streamlit app, you might want to log this or provide feedback
        # st.error("Failed to extract text from PDF.") # Can't use st.error here directly
        return "" # Return empty string on error
    return text


async def _summarize_chunk_async(chunk, streamlit_ref=None, chunk_num=0, total_chunks=0):
    """Helper function to summarize a single chunk asynchronously."""
    try:
        if streamlit_ref:
            streamlit_ref.info(f"Summarizing chunk {chunk_num}/{total_chunks}...")
        print(f"Summarizing chunk {chunk_num}/{total_chunks}...")

        response = await groq_async_client.chat.completions.create( # <--- AWAIT IS CRUCIAL HERE
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Summarize the following text concisely. Focus on key ideas and main points."},
                {"role": "user", "content": chunk}
            ],
        )
        return response.choices[0].message.content
    except APIStatusError as e:
        if streamlit_ref:
            streamlit_ref.error(f"Groq API Error for chunk {chunk_num}: {e.message} (Code: {e.code})")
        print(f"Groq API Error for chunk {chunk_num}: {e.message} (Code: {e.code})")
        return None
    except Exception as e:
        if streamlit_ref:
            streamlit_ref.error(f"Unexpected error summarizing chunk {chunk_num}: {e}")
        print(f"Unexpected error summarizing chunk {chunk_num}: {e}")
        return None

async def summarize_text_async(text, streamlit_ref=None): # <--- RETAIN 'async def' AND '_async' SUFFIX
    """
    Summarizes large texts by chunking them and then combining summaries, asynchronously.
    """
    if not text:
        return "No text provided to summarize."

    # Define chunking parameters (adjust as needed for token limits vs. desired chunk size)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=12000,   # Approx 3000 tokens (1 token ~ 4 chars). Adjust based on model limit.
        chunk_overlap=200,  # Overlap helps maintain context between chunks
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(text)

    if not chunks:
        return "No meaningful chunks could be created from the text."

    # Summarize each chunk concurrently
    tasks = []
    for i, chunk in enumerate(chunks):
        tasks.append(_summarize_chunk_async(chunk, streamlit_ref, i + 1, len(chunks)))

    chunk_summaries = await asyncio.gather(*tasks) # <--- AWAIT ALL CHUNK SUMMARIES

    # Filter out any None values from failed summaries
    chunk_summaries = [s for s in chunk_summaries if s is not None]

    # Combine or Summarize the Summaries
    if not chunk_summaries:
        return "Could not generate any summaries for the provided text chunks."

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries_text = "\n\n".join(chunk_summaries)

    if streamlit_ref:
        streamlit_ref.info("Combining and finalising summary...")
    print("Combining and finalising summary...")

    try:
        final_summary_response = await groq_async_client.chat.completions.create( # <--- AWAIT IS CRUCIAL HERE
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original document. Ensure no information is lost from the sub-summaries."},
                {"role": "user", "content": combined_summaries_text}
            ]
        )
        return final_summary_response.choices[0].message.content
    except APIStatusError as e:
        if streamlit_ref:
            streamlit_ref.error(f"Groq API Error combining summaries: {e.message} (Code: {e.code})")
        print(f"Groq API Error combining summaries: {e.message} (Code: {e.code})")
        return combined_summaries_text + f"\n\n(Note: Final summary combination failed due to API error: {e.message})"
    except Exception as e:
        if streamlit_ref:
            streamlit_ref.error(f"Unexpected error combining summaries: {e}")
        print(f"Unexpected error combining summaries: {e}")
        return combined_summaries_text + "\n\n(Note: Final summary combination failed due to an unexpected error.)"
