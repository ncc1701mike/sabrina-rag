import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def enrich_video(video_id: str, title: str, description: str, transcript_text: str) -> dict:
    """
    Use Claude to extract structured enrichment from a video's content.
    Returns topics, key_insights, content_type, target_audience.
    """
    client = get_client()

    prompt = f"""Analyze this YouTube video from Sabrina Ramonov's channel about AI and social media strategy.

Title: {title}
Description: {description[:500] if description else 'N/A'}
Transcript (first 3000 chars): {transcript_text[:3000] if transcript_text else 'N/A'}

Return a JSON object with these exact fields:
- topics: list of 3-8 specific topics covered (e.g. ["prompt engineering", "content creation", "LinkedIn strategy"])
- key_insights: list of 3-5 key actionable insights or takeaways as strings
- content_type: one of ["tutorial", "strategy", "case_study", "opinion", "interview", "tools_review"]
- target_audience: brief string describing who this content is for

Return ONLY valid JSON, no markdown, no other text."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(text)
