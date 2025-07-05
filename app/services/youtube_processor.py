import re
import asyncio
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, VideoUnavailable
from groq import APIStatusError, RateLimitError
from xml.etree.ElementTree import ParseError
from .groq_client import client as groq_async_client

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
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry["text"] for entry in transcript])
            return transcript_text, None
        except TranscriptsDisabled:
            return None, f"Transcripts are disabled for video ID: {video_id}."
        except VideoUnavailable:
            return None, f"Video ID {video_id} is unavailable."
        except ParseError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return None, "Failed to fetch transcript due to invalid API response (parsing error)."
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return None, f"Failed to fetch transcript: {str(e)}"

async def summarize_transcript(transcript, retries=3, delay=2):
    """Summarizes a YouTube video transcript using Groq."""
    if not transcript:
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
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if attempt < retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            return "Failed to summarize transcript due to API rate limit."
        except APIStatusError as e:
            return f"Failed to summarize transcript due to API error: {e.message}"
        except Exception as e:
            return f"Failed to summarize transcript due to an unexpected error: {e}"