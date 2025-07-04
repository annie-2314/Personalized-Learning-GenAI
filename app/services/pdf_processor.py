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