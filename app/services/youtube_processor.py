import re
import asyncio
import logging
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable
from groq import APIStatusError, RateLimitError
from xml.etree.ElementTree import ParseError
from .groq_client import client as groq_async_client

logging.basicConfig(level=logging.INFO, filename='app_logs.log')

def extract_video_id(url):
    """Extracts the YouTube video ID from a URL."""
    try:
        regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(regex, url)
        return match.group(1) if match else None
    except Exception:
        return None

async def get_transcript(url, retries=3, delay=2):
    """Fetches the transcript for a YouTube video with retries."""
    video_id = extract_video_id(url)
    if not video_id:
        return None, "Invalid YouTube URL."

    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            transcript = await asyncio.to_thread(YouTubeTranscriptApi.get_transcript, video_id)
            transcript_text = " ".join([entry["text"] for entry in transcript])
            logging.info(f"Successfully fetched transcript for video ID: {video_id}")
            return transcript_text, None
        except TranscriptsDisabled:
            logging.warning(f"Transcripts disabled for video ID: {video_id}")
            return None, f"Transcripts are disabled for video ID: {video_id}."
        except VideoUnavailable:
            logging.error(f"Video unavailable for video ID: {video_id}")
            return None, f"Video ID {video_id} is unavailable."
        except ParseError:
            if attempt < retries - 1:
                logging.warning(f"Parse error for video ID: {video_id}, attempt {attempt + 1}/{retries}")
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            logging.error(f"Failed to parse transcript for video ID: {video_id} after {retries} attempts")
            return None, "Failed to fetch transcript due to invalid API response (parsing error)."
        except Exception as e:
            if attempt < retries - 1:
                logging.warning(f"General error for video ID: {video_id}, attempt {attempt + 1}/{retries}: {str(e)}")
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            logging.error(f"Failed to fetch transcript for video ID: {video_id} after {retries} attempts: {str(e)}")
            return None, f"Failed to fetch transcript: {str(e)}"

async def summarize_transcript(transcript, retries=3, delay=2):
    """Summarizes a YouTube video transcript using Groq."""
    if not transcript:
        logging.error("No transcript provided to summarize.")
        return "No transcript provided to summarize."

    for attempt in range(retries):
        try:
            await asyncio.sleep(1)  # Delay to avoid rate limits
            response = await groq_async_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "Summarize the following transcript concisely, focusing on key points."},
                    {"role": "user", "content": transcript}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            logging.info("Successfully summarized transcript.")
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if attempt < retries - 1:
                logging.warning(f"Rate limit hit, attempt {attempt + 1}/{retries}")
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            logging.error("Failed to summarize due to rate limit after retries.")
            return "Failed to summarize transcript due to API rate limit."
        except APIStatusError as e:
            logging.error(f"API error during summarization: {e.message}")
            return f"Failed to summarize transcript due to API error: {e.message}"
        except Exception as e:
            logging.error(f"Unexpected error during summarization: {e}")
            return f"Failed to summarize transcript due to an unexpected error: {e}"