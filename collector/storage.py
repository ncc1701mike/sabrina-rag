from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def upsert_transcript(record: dict) -> bool:
    """
    Upsert a single transcript record to Supabase.
    Returns True on success, False on failure.
    """
    sb = get_supabase()
    try:
        sb.table("transcripts").upsert(record).execute()
        return True
    except Exception as e:
        print(f"  Supabase upsert failed for {record.get('video_id')}: {e}")
        return False

def get_existing_video_ids() -> set[str]:
    """
    Return set of video_ids already in the database.
    Used to skip videos we've already collected.
    """
    sb = get_supabase()
    result = sb.table("transcripts") \
        .select("video_id") \
        .execute()
    return {row["video_id"] for row in (result.data or [])}
