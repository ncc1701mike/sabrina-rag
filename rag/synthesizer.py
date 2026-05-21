import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def synthesize(query: str, chunks: list[dict]) -> str:
    """
    Use Claude to synthesize an answer from retrieved transcript chunks.
    """
    client = get_client()

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        video_id = chunk.get("video_id", "unknown")
        tags     = ", ".join(chunk.get("topics", []))
        text     = chunk.get("text", "")
        context_parts.append(
            f"[Excerpt {i} | Video: {video_id} | Topics: {tags}]\n{text}"
        )

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a strategic advisor helping someone learn from Sabrina Ramonov's YouTube content on AI tools and social media strategy. You have access to excerpts from her video transcripts.

Question: {query}

Relevant video excerpts:
{context}

Provide a clear, actionable answer grounded in the excerpts above. Reference specific strategies or insights Sabrina mentions where relevant. Focus on practical takeaways the user can apply."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
