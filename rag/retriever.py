from dotenv import load_dotenv

load_dotenv()

from collector.storage import get_supabase
from enrichment.embedder import embed_texts


def retrieve(query: str, top_k: int = 8, topics: list[str] = None) -> list[dict]:
    """
    Retrieve relevant chunks from Supabase via cosine similarity.
    Optionally filter by topics (OR logic — any matching topic qualifies).
    Returns list of chunk dicts: id, video_id, chunk_index, text, topics, similarity.
    """
    sb = get_supabase()

    query_embedding = embed_texts([query])[0]

    params = {
        "query_embedding": query_embedding,
        "match_count":     top_k,
    }
    if topics:
        params["filter_topics"] = topics

    result = sb.rpc("match_chunks", params).execute()
    return result.data or []
