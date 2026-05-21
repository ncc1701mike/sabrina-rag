import tiktoken

CHUNK_SIZE = 400   # tokens per chunk
OVERLAP    = 50    # token overlap between chunks


def chunk_text(text: str, video_id: str) -> list[dict]:
    """
    Split transcript text into overlapping token-bounded chunks.
    Returns list of dicts: video_id, chunk_index, text, chunk_token_count.
    """
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    chunks = []
    chunk_index = 0
    start = 0

    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_str = enc.decode(chunk_tokens)

        chunks.append({
            "video_id":          video_id,
            "chunk_index":       chunk_index,
            "text":              chunk_str,
            "chunk_token_count": len(chunk_tokens),
        })

        chunk_index += 1
        if end == len(tokens):
            break
        start = end - OVERLAP

    return chunks
