from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch transcript for a video.
    Returns (transcript_text, source) where source is 'manual', 'auto', or 'none'.
    Prioritizes manual transcripts over auto-generated.
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try manual first
        try:
            transcript = transcript_list.find_manually_created_transcript(['en'])
            source = 'manual'
        except Exception:
            # Fall back to auto-generated
            transcript = transcript_list.find_generated_transcript(['en'])
            source = 'auto'

        entries = transcript.fetch()
        full_text = " ".join(
            entry.get("text", "").strip()
            for entry in entries
        ).strip()

        return full_text, source

    except (NoTranscriptFound, TranscriptsDisabled):
        return "", "none"
    except Exception as e:
        print(f"  Error fetching transcript for {video_id}: {e}")
        return "", "none"
