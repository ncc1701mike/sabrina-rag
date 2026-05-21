from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using OpenAI text-embedding-3-small (1536 dims).
    Returns a list of embedding vectors in the same order as the input.
    """
    client = get_client()
    # Newlines degrade embedding quality per OpenAI's recommendation
    cleaned = [t.replace("\n", " ") for t in texts]

    response = client.embeddings.create(
        input=cleaned,
        model="text-embedding-3-small",
    )

    return [item.embedding for item in response.data]
