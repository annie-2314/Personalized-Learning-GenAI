<<<<<<< HEAD
# import io
# from pypdf import PdfReader
# from .groq_client import client
# from langchain_text_splitters import RecursiveCharacterTextSplitter


# def extract_text_from_pdf(uploaded_file):
#     """
#     Extracts text from an uploaded Streamlit PDF file object.
#     """
#     file_stream = io.BytesIO(uploaded_file.getvalue())
#     reader = PdfReader(file_stream)
#     text = ""
#     for page in reader.pages:
#         text += page.extract_text() + "\n"
#     return text

# def summarize_text(text, streamlit_ref=None):
#     # --- Step 1: Define Chunking Parameters ---
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=12000,
#         chunk_overlap=200,
#         length_function=len,
#         is_separator_regex=False,
#     )
#     chunks = text_splitter.split_text(text)

#     # --- Step 2: Summarize Each Chunk ---
#     chunk_summaries = []
#     for i, chunk in enumerate(chunks):
#         if streamlit_ref:
#             streamlit_ref.info(f"Summarizing chunk {i+1}/{len(chunks)}...")
#         print(f"Summarizing chunk {i+1}/{len(chunks)}...")

#         try:
#             response = client.chat.completions.create(
#                 model="llama3-8b-8192",
#                 messages=[
#                     {"role": "system", "content": "Summarize the following text concisely. Focus on key ideas and main points."},
#                     {"role": "user", "content": chunk}
#                 ]
#             )
#             chunk_summaries.append(response.choices[0].message.content)
#         except Exception as e:
#             if streamlit_ref:
#                 streamlit_ref.error(f"Error summarizing chunk {i+1}: {e}")
#             print(f"Error summarizing chunk {i+1}: {e}")
#             continue

#     # --- Step 3: Combine or Summarize the Summaries ---
#     if not chunk_summaries:
#         return "Could not generate summary for the provided text."

#     if len(chunk_summaries) == 1:
#         return chunk_summaries[0]

#     combined_summaries_text = "\n\n".join(chunk_summaries)

#     if streamlit_ref:
#         streamlit_ref.info("Combining and finalising summary...")
#     print("Combining and finalising summary...")

#     try:
#         final_summary_response = client.chat.completions.create(
#             model="llama3-8b-8192",
#             messages=[
#                 {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original document."},
#                 {"role": "user", "content": combined_summaries_text}
#             ]
#         )
#         return final_summary_response.choices[0].message.content
#     except Exception as e:
#         if streamlit_ref:
#             streamlit_ref.error(f"Error combining summaries: {e}")
#         print(f"Error combining summaries: {e}")
#         return combined_summaries_text + "\n\n(Note: Final summary combination failed due to API limits or other error.)"

import io
from pypdf import PdfReader
from .groq_client import client
from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_pdf(uploaded_file):
    file_stream = io.BytesIO(uploaded_file.getvalue())
    reader = PdfReader(file_stream)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def summarize_text(text, streamlit_ref=None):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=12000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        if streamlit_ref:
            streamlit_ref.info(f"Summarizing chunk {i+1}/{len(chunks)}...")
        print(f"Summarizing chunk {i+1}/{len(chunks)}...")
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Summarize the following text concisely. Focus on key ideas and main points."},
                    {"role": "user", "content": chunk}
                ]
            )
            chunk_summaries.append(response.choices[0].message.content)
        except Exception as e:
            if streamlit_ref:
                streamlit_ref.error(f"Error summarizing chunk {i+1}: {e}")
            print(f"Error summarizing chunk {i+1}: {e}")
            continue
    if not chunk_summaries:
        return "Could not generate summary for the provided text."
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]
    combined_summaries_text = "\n\n".join(chunk_summaries)
    if streamlit_ref:
        streamlit_ref.info("Combining and finalising summary...")
    print("Combining and finalising summary...")
    try:
        final_summary_response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original document."},
                {"role": "user", "content": combined_summaries_text}
            ]
        )
        return final_summary_response.choices[0].message.content
    except Exception as e:
        if streamlit_ref:
            streamlit_ref.error(f"Error combining summaries: {e}")
        print(f"Error combining summaries: {e}")
        return combined_summaries_text + "\n\n(Note: Final summary combination failed due to API limits or other error.)"
=======
# app/services/pdf_processor.py

import io
import fitz  # PyMuPDF
import asyncio
from groq import APIStatusError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .groq_client import client as groq_async_client # Correctly import the async client

def extract_text_from_pdf(uploaded_file):
    """
    Extracts text from an uploaded Streamlit PDF file object using PyMuPDF.
    This function is SYNCHRONOUS.
    """
    file_bytes = uploaded_file.getvalue() # Get bytes content from Streamlit UploadedFile
    file_stream = io.BytesIO(file_bytes) # Wrap bytes in a BytesIO object for PyMuPDF

    text = ""
    try:
        # Pass the BytesIO object directly to fitz.open (it's a file-like object)
        with fitz.open(stream=file_stream, filetype="pdf") as doc: # Corrected this line
            for page in doc:
                extracted_page_text = page.get_text()
                if extracted_page_text:
                    text += extracted_page_text + "\n"
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
    return text


async def _summarize_chunk_async(chunk, streamlit_ref=None, chunk_num=0, total_chunks=0):
    """
    Helper function to summarize a single text chunk asynchronously using Groq.
    """
    try:
        if streamlit_ref:
            streamlit_ref.info(f"Summarizing chunk {chunk_num}/{total_chunks}...")
        print(f"Summarizing chunk {chunk_num}/{total_chunks}...")

        response = await groq_async_client.chat.completions.create( # AWAIT IS CRUCIAL HERE
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Summarize the following text concisely. Focus on key ideas and main points."},
                {"role": "user", "content": chunk}
            ],
            temperature=0.7,
            max_tokens=1024, # Ensure this is within model limits for a chunk summary
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

async def summarize_text_async(text, streamlit_ref=None):
    """
    Summarizes large texts by chunking them and then combining summaries, asynchronously.
    """
    if not text:
        return "No text provided to summarize."

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=12000,   # Approx 3000 tokens (1 token ~ 4 chars). Adjust based on model limit.
        chunk_overlap=200,  # Overlap helps maintain context between chunks
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(text)

    if not chunks:
        return "No meaningful chunks could be created from the text."

    tasks = []
    for i, chunk in enumerate(chunks):
        tasks.append(_summarize_chunk_async(chunk, streamlit_ref, i + 1, len(chunks)))

    if streamlit_ref:
        streamlit_ref.info(f"Processing {len(chunks)} text chunks...")
    print(f"Processing {len(chunks)} text chunks...")

    chunk_summaries = await asyncio.gather(*tasks)

    chunk_summaries = [s for s in chunk_summaries if s is not None]

    if not chunk_summaries:
        return "Could not generate any summaries for the provided text chunks due to errors."

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries_text = "\n\n".join(chunk_summaries)

    if streamlit_ref:
        streamlit_ref.info("Combining and finalising summary...")
    print("Combining and finalising summary...")

    try:
        final_summary_response = await groq_async_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original document. Ensure no information is lost from the sub-summaries."},
                {"role": "user", "content": combined_summaries_text}
            ],
            temperature=0.7,
            max_tokens=2048, # Adjust for final summary
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
>>>>>>> d74278b28538bb94c82591bdf8c53d6da903f04a
