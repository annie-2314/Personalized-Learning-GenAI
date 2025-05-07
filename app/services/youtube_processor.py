from youtube_transcript_api import YouTubeTranscriptApi
from services.groq_client import client

def get_video_id(url):
    # Extract video ID from URL
    import re
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_transcript(video_url):
    video_id = get_video_id(video_url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join([entry['text'] for entry in transcript])
    return text

def summarize_transcript(transcript_text):
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": "Summarize the following transcript:"},
            {"role": "user", "content": transcript_text}
        ]
    )
    return response.choices[0].message.content
