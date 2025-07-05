import re
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from groq import APIStatusError, RateLimitError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .groq_client import client as groq_async_client

def extract_video_id(url):
    """Extracts YouTube video ID from a URL."""
    patterns = [
        r"(?:v=|v/|embed/|youtu.be/|watch\?v=)([a-zA-Z0-9_-]{11})",
        r"shorts/([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def get_transcript(video_url):
    """Extracts transcript from a YouTube video URL."""
    video_id = extract_video_id(video_url)
    if not video_id:
        return None, "Could not extract video ID from the provided URL."

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join(entry['text'] for entry in transcript_list)
        return text, None
    except NoTranscriptFound:
        return None, f"No transcript found for video ID: {video_id} (URL: {video_url}). The video might not have captions."
    except TranscriptsDisabled:
        return None, f"Transcripts are disabled for video ID: {video_id} (URL: {video_url})."
    except Exception as e:
        return None, f"An unexpected error occurred while fetching transcript for video ID: {video_id} (URL: {video_url}). Error: {e}"

async def summarize_transcript(transcript_text, retries=3, delay=2):
    """Summarizes a YouTube transcript asynchronously using Groq with retries."""
    if not transcript_text:
        return "No transcript available to summarize."

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=20000,  # Increased to reduce API calls
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_text(transcript_text)
    chunk_summaries = []

    for i, chunk in enumerate(chunks):
        for attempt in range(retries):
            try:
                await asyncio.sleep(1)  # Delay to avoid rate limits
                response = await groq_async_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": "Summarize the following transcript chunk concisely."},
                        {"role": "user", "content": chunk}
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                )
                chunk_summaries.append(response.choices[0].message.content)
                break
            except RateLimitError:
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    continue
                chunk_summaries.append(None)
            except APIStatusError:
                chunk_summaries.append(None)
                break
            except Exception:
                chunk_summaries.append(None)
                break

    chunk_summaries = [s for s in chunk_summaries if s is not None]
    if not chunk_summaries:
        return "Could not generate summary for the provided transcript due to errors."

    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries_text = "\n\n".join(chunk_summaries)
    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            final_summary_response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Combine the following individual summaries into a comprehensive and cohesive final summary of the original YouTube transcript."},
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
            return combined_summaries_text + "\n\n(Note: Final transcript summary combination failed due to API rate limit.)"
        except APIStatusError as e:
            return combined_summaries_text + f"\n\n(Note: Final transcript summary combination failed due to API error: {e.message})"
        except Exception as e:
            return combined_summaries_text + f"\n\n(Note: Final transcript summary combination failed due to an unexpected error: {e})"