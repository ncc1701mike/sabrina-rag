-- ============================================================
-- Run this entire file in the Supabase SQL editor.
-- It creates the chunks table and the match_chunks RPC function
-- used by the RAG retriever.
-- ============================================================

-- 1. Enable pgvector (safe to run if already enabled)
create extension if not exists vector;

-- 2. Chunks table
create table if not exists chunks (
    id                uuid        primary key default gen_random_uuid(),
    video_id          text        not null,
    chunk_index       integer     not null,
    text              text        not null,
    embedding         vector(1536),
    topics            text[],
    chunk_token_count integer,
    created_at        timestamptz default now()
);

-- 3. Indexes
create index if not exists chunks_embedding_idx
    on chunks using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

create index if not exists chunks_video_id_idx on chunks (video_id);

-- 4. Enrichment columns on transcripts (safe to run if columns exist)
alter table transcripts
    add column if not exists topics          text[],
    add column if not exists key_insights    text,
    add column if not exists content_type    text,
    add column if not exists target_audience text;

-- 5. match_chunks RPC function
--    Called by the Python retriever via sb.rpc("match_chunks", {...})
create or replace function match_chunks(
    query_embedding vector(1536),
    match_count     integer  default 8,
    filter_topics   text[]   default null
)
returns table (
    id                uuid,
    video_id          text,
    chunk_index       integer,
    text              text,
    topics            text[],
    chunk_token_count integer,
    similarity        float
)
language plpgsql
as $$
begin
    return query
    select
        c.id,
        c.video_id,
        c.chunk_index,
        c.text,
        c.topics,
        c.chunk_token_count,
        1 - (c.embedding <=> query_embedding) as similarity
    from chunks c
    where (
        filter_topics is null
        or c.topics && filter_topics   -- && = array overlap (any element matches)
    )
    order by c.embedding <=> query_embedding
    limit match_count;
end;
$$;
