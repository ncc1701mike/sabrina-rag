from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import requests
from http.cookiejar import MozillaCookieJar
import os

COOKIES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "cookies.txt"
)

def get_api():
    """Return a YouTubeTranscriptApi instance, with cookies if available."""
    if os.path.exists(COOKIES_PATH):
        session = requests.Session()
        cj = MozillaCookieJar()
        cj.load(COOKIES_PATH, ignore_discard=True, ignore_expires=True)
        session.cookies = cj
        return YouTubeTranscriptApi(http_client=session)
    return YouTubeTranscriptApi()

def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch transcript for a video.
    Returns (transcript_text, source) where source is 'manual', 'auto', or 'none'.
    Prioritizes manual transcripts over auto-generated.
    """
    try:
        api = get_api()
        transcript_list = api.list(video_id)

        # Try manual first
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
            source = 'manual'
        except Exception:
            transcript = transcript_list.find_generated_transcript(['en'])
            source = 'auto'

        entries = transcript.fetch()
        full_text = " ".join(
            entry.text.strip()
            for entry in entries
        ).strip()

        return full_text, source

    except (NoTranscriptFound, TranscriptsDisabled):
        return "", "none"
    except Exception as e:
        print(f"  Error fetching transcript for {video_id}: {e}")
        return "", "none"
