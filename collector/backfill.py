#!/usr/bin/env python3
"""
Backfill transcripts for all videos stored with transcript_source = 'none'.
Runs only on missing transcripts — safe to run multiple times.
"""

import time
from datetime import datetime
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

from collector.transcripts import fetch_transcript
from collector.storage import get_supabase

DELAY_SECONDS = 0.5

def run_backfill():
    sb = get_supabase()

    print("Fetching videos with missing transcripts...")
    result = sb.table("transcripts") \
        .select("video_id, title") \
        .eq("transcript_source", "none") \
        .execute()

    missing = result.data or []
    print(f"Videos needing transcripts: {len(missing)}")

    if not missing:
        print("Nothing to backfill.")
        return

    success = 0
    still_none = 0
    failed = 0

    for row in tqdm(missing, desc="Backfilling"):
        video_id = row["video_id"]
        transcript_text, source = fetch_transcript(video_id)
        word_count = len(transcript_text.split()) if transcript_text else 0

        if source == "none":
            still_none += 1
        else:
            success += 1

        try:
            sb.table("transcripts").update({
                "transcript_text":   transcript_text,
                "transcript_source": source,
                "word_count":        word_count,
                "fetched_at":        datetime.utcnow().isoformat(),
            }).eq("video_id", video_id).execute()
        except Exception as e:
            print(f"  Update failed for {video_id}: {e}")
            failed += 1

        time.sleep(DELAY_SECONDS)

    print("\n" + "=" * 60)
    print("Backfill complete.")
    print(f"  Got transcript:    {success}")
    print(f"  Still none:        {still_none}")
    print(f"  Failed to update:  {failed}")
    print("=" * 60)

if __name__ == "__main__":
    run_backfill()
