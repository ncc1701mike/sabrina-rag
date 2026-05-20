#!/usr/bin/env python3
"""
Postcraft Sabrina RAG - Transcript Collector
Usage: python collector/run.py

Fetches all video transcripts from @sabrina_ramonov and stores in Supabase.
"""

import time
from datetime import datetime
from tqdm import tqdm
from collector.channel import get_channel_id, get_all_video_ids, get_video_details
from collector.transcripts import fetch_transcript
from collector.storage import upsert_transcript, get_existing_video_ids

CHANNEL_HANDLE = "@sabrina_ramonov"
DELAY_SECONDS  = 1.0   # polite delay between transcript requests

def run():
    print("=" * 60)
    print("Sabrina RAG — Transcript Collector")
    print("=" * 60)

    # Step 1: Get channel ID
    print(f"\n[1] Resolving channel handle: {CHANNEL_HANDLE}")
    channel_id = get_channel_id(CHANNEL_HANDLE)
    print(f"    Channel ID: {channel_id}")

    # Step 2: Get all video IDs
    print(f"\n[2] Fetching video list...")
    videos = get_all_video_ids(channel_id)
    video_ids = [v["video_id"] for v in videos]
    video_map = {v["video_id"]: v for v in videos}

    # Step 3: Get detailed metadata in batches
    print(f"\n[3] Fetching video metadata for {len(video_ids)} videos...")
    details = get_video_details(video_ids)

    # Step 4: Check which videos we already have
    print(f"\n[4] Checking existing records in Supabase...")
    existing = get_existing_video_ids()
    new_videos = [vid for vid in video_ids if vid not in existing]
    print(f"    Already collected: {len(existing)}")
    print(f"    New to collect:    {len(new_videos)}")

    if not new_videos:
        print("\nAll videos already collected. Nothing to do.")
        return

    # Step 5: Fetch transcripts and store
    print(f"\n[5] Collecting transcripts...")
    success = 0
    skipped = 0
    failed  = 0

    for video_id in tqdm(new_videos, desc="Collecting"):
        base   = video_map.get(video_id, {})
        detail = details.get(video_id, {})

        transcript_text, source = fetch_transcript(video_id)

        if source == "none":
            skipped += 1

        word_count = len(transcript_text.split()) if transcript_text else 0

        record = {
            "video_id":          video_id,
            "title":             base.get("title", ""),
            "description":       detail.get("description", ""),
            "published_at":      base.get("published_at"),
            "duration_seconds":  detail.get("duration_seconds", 0),
            "view_count":        detail.get("view_count", 0),
            "like_count":        detail.get("like_count", 0),
            "channel_id":        base.get("channel_id", ""),
            "channel_title":     base.get("channel_title", ""),
            "transcript_text":   transcript_text,
            "transcript_source": source,
            "word_count":        word_count,
            "fetched_at":        datetime.utcnow().isoformat(),
            "tags":              detail.get("tags", []),
            "thumbnail_url":     base.get("thumbnail_url", ""),
        }

        ok = upsert_transcript(record)
        if ok:
            success += 1
        else:
            failed += 1

        time.sleep(DELAY_SECONDS)

    # Summary
    print("\n" + "=" * 60)
    print("Collection complete.")
    print(f"  Collected:     {success}")
    print(f"  No transcript: {skipped}")
    print(f"  Failed:        {failed}")
    print(f"  Total:         {len(new_videos)}")
    print("=" * 60)

if __name__ == "__main__":
    run()
