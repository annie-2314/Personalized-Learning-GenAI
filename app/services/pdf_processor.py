import io
import fitz
import asyncio
from groq import APIStatusError, RateLimitError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .groq_client import client as groq_async_client

def extract_text_from_pdf(uploaded_file):
    """Extracts text from an uploaded Streamlit PDF file object using PyMuPDF."""
    file_bytes = uploaded_file.getvalue()
    file_stream = io.BytesIO(file_bytes)
    text = ""
    try:
        with fitz.open(stream=file_stream, filetype="pdf") as doc:
            for page in doc:
                extracted_page_text = page.get_text()
                if extracted_page_text:
                    text += extracted_page_text + "\n"
        return text.strip() if text.strip() else ""
    except Exception:
        return ""

async def _summarize_chunk_async(chunk, chunk_num=0, total_chunks=0, retries=3, delay=2):
    """Helper function to summarize a single text chunk asynchronously using Groq."""
    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Summarize the following text concisely. Focus on key ideas and main points."},
                    {"role": "user", "content": chunk}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return None
        except APIStatusError:
            return None
        except Exception:
            return None

async def summarize_text_async(text, retries=3, delay=2):
    """Summarizes large texts by chunking them and combining summaries asynchronously."""
    if not text:
        return "No text provided to summarize."

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=12000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(text)

    if not chunks:
        return "No meaningful chunks could be created from the text."

    tasks = []
    for i, chunk in enumerate(chunks):
        tasks.append(_summarize_chunk_async(chunk, i + 1, len(chunks), retries, delay))

    chunk_summaries = await asyncio.gather(*tasks)
    chunk_summaries = [s for s in chunk_summaries if s is not None]

    if not chunk_summaries:
        return "Could not generate any summaries for the provided text chunks due to errors."

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries_text = "\n\n".join(chunk_summaries)
    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            final_summary_response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original document. Ensure no information is lost from the sub-summaries."},
                    {"role": "user", "content": combined_summaries_text}
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            return final_summary_response.choices[0].message.content
        except RateLimitError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return combined_summaries_text + "\n\n(Note: Final summary combination failed due to API rate limit.)"
        except APIStatusError as e:
            return combined_summaries_text + f"\n\n(Note: Final summary combination failed due to API error: {e.message})"
        except Exception as e:
            return combined_summaries_text + f"\n\n(Note: Final summary combination failed due to an unexpected error: {e})"