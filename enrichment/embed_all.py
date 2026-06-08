#!/usr/bin/env python3
"""
Embed all enriched transcripts into transcript_chunks.
Run after enrichment/pipeline.py completes.
"""
import sys
sys.path.insert(0, '/Users/michaeldoran/sabrina-rag')

from dotenv import load_dotenv
load_dotenv('/Users/michaeldoran/sabrina-rag/.env')

from collector.storage import get_supabase
from enrichment.chunker import chunk_text
from enrichment.embedder import embed_texts

sb = get_supabase()

enriched = sb.table('video_enrichments') \
    .select('video_id, topic_tags, strategic_value_score') \
    .execute()

print(f'Videos to embed: {len(enriched.data)}')

max_views_result = sb.table('transcripts') \
    .select('view_count') \
    .order('view_count', desc=True) \
    .limit(1) \
    .execute()
max_views = max_views_result.data[0]['view_count'] if max_views_result.data else 1000000

total_chunks = 0
failed = 0
BATCH_SIZE = 50

for i, enrichment in enumerate(enriched.data):
    video_id = enrichment['video_id']

    transcript_result = sb.table('transcripts') \
        .select('transcript_text, view_count') \
        .eq('video_id', video_id) \
        .single() \
        .execute()

    if not transcript_result.data:
        continue

    transcript_text = transcript_result.data.get('transcript_text', '') or ''
    view_count = transcript_result.data.get('view_count', 0) or 0

    if not transcript_text or len(transcript_text.split()) < 20:
        continue

    chunks = chunk_text(text=transcript_text, video_id=video_id)
    if not chunks:
        continue

    texts = [c['text'] for c in chunks]
    view_weight = min(view_count / max(max_views, 1), 1.0)

    for b in range(0, len(texts), BATCH_SIZE):
        batch_texts  = texts[b:b+BATCH_SIZE]
        batch_chunks = chunks[b:b+BATCH_SIZE]

        try:
            embeddings = embed_texts(batch_texts)
        except Exception as e:
            print(f'  Embed error {video_id}: {e}')
            failed += 1
            continue

        records = []
        for chunk, embedding in zip(batch_chunks, embeddings):
            records.append({
                'video_id':          video_id,
                'chunk_index':       chunk.get('chunk_index', 0),
                'chunk_text':        chunk['text'],
                'chunk_summary':     '',
                'topic_tags':        enrichment.get('topic_tags', []),
                'embedding':         embedding,
                'view_count_weight': view_weight,
                'word_count':        len(chunk['text'].split()),
            })

        try:
            sb.table('transcript_chunks').upsert(
                records,
                on_conflict='video_id,chunk_index'
            ).execute()
            total_chunks += len(records)
        except Exception as e:
            print(f'  DB error {video_id}: {e}')
            failed += 1

    if (i + 1) % 100 == 0:
        print(f'  Progress: {i+1}/{len(enriched.data)} | {total_chunks} chunks | {failed} errors')

print(f'\nDone.')
print(f'Total chunks embedded: {total_chunks}')
print(f'Errors: {failed}')
