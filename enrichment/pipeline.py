#!/usr/bin/env python3
"""
Enrichment pipeline: reads transcripts from Supabase, enriches with Claude,
chunks, embeds with OpenAI, and stores chunks back to Supabase.

Usage:
  python -m enrichment.pipeline              # process all unenriched videos
  python -m enrichment.pipeline --limit 5   # process first 5 (for testing)
  python -m enrichment.pipeline --dry-run   # enrich only, no DB writes
"""

import argparse
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

from collector.storage import get_supabase
from enrichment.enricher import enrich_video
from enrichment.chunker import chunk_text
from enrichment.embedder import embed_texts

EMBED_BATCH = 20   # chunks to embed per OpenAI call


def get_unenriched_videos(sb, limit: int = None) -> list[dict]:
    query = (
        sb.table("transcripts")
        .select("video_id, title, description, transcript_text")
        .neq("transcript_source", "none")
        .neq("transcript_text", "")
    )
    if limit:
        query = query.limit(limit)
    result = query.execute()
    videos = result.data or []

    if not videos:
        return []

    # Exclude videos whose chunks are already stored
    processed = {
        row["video_id"]
        for row in (sb.table("chunks").select("video_id").execute().data or [])
    }
    return [v for v in videos if v["video_id"] not in processed]


def run_pipeline(limit: int = None, dry_run: bool = False):
    sb = get_supabase()

    print("Fetching unenriched videos...")
    videos = get_unenriched_videos(sb, limit=limit)

    if not videos:
        print("No new videos to process.")
        return

    print(f"Processing {len(videos)} videos...")
    success = 0
    failed  = 0

    for video in tqdm(videos, desc="Enriching"):
        video_id        = video["video_id"]
        title           = video.get("title", "")
        description     = video.get("description", "")
        transcript_text = video.get("transcript_text", "")

        if not transcript_text or len(transcript_text.strip()) < 50:
            continue

        try:
            # 1. Enrich with Claude
            enrichment = enrich_video(video_id, title, description, transcript_text)
            topics = enrichment.get("topics", [])

            if dry_run:
                print(f"\n  [{video_id}] {title[:60]}")
                print(f"    Topics:  {topics}")
                print(f"    Type:    {enrichment.get('content_type')}")
                continue

            # 2. Write enrichment metadata back to transcripts row
            sb.table("transcripts").update({
                "topics":          topics,
                "key_insights":    json.dumps(enrichment.get("key_insights", [])),
                "content_type":    enrichment.get("content_type", ""),
                "target_audience": enrichment.get("target_audience", ""),
            }).eq("video_id", video_id).execute()

            # 3. Chunk
            chunks = chunk_text(transcript_text, video_id)
            for chunk in chunks:
                chunk["topics"] = topics

            # 4. Embed in batches
            texts_to_embed = [c["text"] for c in chunks]
            all_embeddings = []
            for i in range(0, len(texts_to_embed), EMBED_BATCH):
                batch_embeddings = embed_texts(texts_to_embed[i : i + EMBED_BATCH])
                all_embeddings.extend(batch_embeddings)

            # 5. Store chunks
            records = [
                {
                    "video_id":          c["video_id"],
                    "chunk_index":       c["chunk_index"],
                    "text":              c["text"],
                    "embedding":         emb,
                    "topics":            c["topics"],
                    "chunk_token_count": c["chunk_token_count"],
                }
                for c, emb in zip(chunks, all_embeddings)
            ]
            for i in range(0, len(records), 100):
                sb.table("chunks").insert(records[i : i + 100]).execute()

            success += 1
            time.sleep(0.5)

        except Exception as e:
            print(f"\n  Failed [{video_id}]: {e}")
            failed += 1

    print(f"\nPipeline complete. Success: {success}  Failed: {failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",   type=int, default=None, help="Max videos to process")
    parser.add_argument("--dry-run", action="store_true",    help="Enrich only, no DB writes")
    args = parser.parse_args()
    run_pipeline(limit=args.limit, dry_run=args.dry_run)
