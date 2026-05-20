from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import requests
from http.cookiejar import MozillaCookieJar
import subprocess
import tempfile
import glob
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

def _fetch_via_whisper(video_id: str) -> tuple[str, str]:
    """
    Fallback: download audio with yt-dlp and transcribe with mlx-whisper.
    Used when YouTube's transcript API is blocked.
    """
    try:
        import mlx_whisper
    except ImportError:
        return "", "none"

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--remote-components", "ejs:github",
            "-f", "bestaudio",
            "--no-playlist",
            "-o", os.path.join(tmpdir, "%(id)s.%(ext)s"),
        ]
        if os.path.exists(COOKIES_PATH):
            cmd += ["--cookies", COOKIES_PATH]
        cmd.append(f"https://www.youtube.com/watch?v={video_id}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print(f"  yt-dlp failed for {video_id}: {result.stderr[-200:]}")
            return "", "none"

        files = glob.glob(os.path.join(tmpdir, f"{video_id}.*"))
        if not files:
            return "", "none"

        audio_path = files[0]
        transcription = mlx_whisper.transcribe(
            audio_path,
            path_or_hf_repo="mlx-community/whisper-small-mlx",
            language="en",
            verbose=False,
        )
        text = transcription.get("text", "").strip()
        return text, "whisper"

def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch transcript for a video.
    Tries YouTube's transcript API first; falls back to Whisper if blocked.
    Returns (transcript_text, source) where source is
    'manual', 'auto', 'whisper', or 'none'.
    """
    try:
        api = get_api()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
            source = 'manual'
        except Exception:
            transcript = transcript_list.find_generated_transcript(['en'])
            source = 'auto'

        entries = transcript.fetch()
        full_text = " ".join(entry.text.strip() for entry in entries).strip()
        return full_text, source

    except (NoTranscriptFound, TranscriptsDisabled):
        return "", "none"
    except Exception:
        # YouTube API blocked — fall back to Whisper
        return _fetch_via_whisper(video_id)
