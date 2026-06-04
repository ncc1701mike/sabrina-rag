#!/usr/bin/env python3
"""
Main query interface for the Sabrina RAG system.

Usage:
  python -m rag.query "How does Sabrina approach LinkedIn content?"
  python -m rag.query "What AI tools does she recommend?" --top-k 12
  python -m rag.query "prompt engineering tips" --topics "prompt engineering" "ChatGPT"
  python -m rag.query "hook strategies" --platforms tiktok instagram --tags short-form-video --save
"""

import argparse
import os
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from rag.retriever import retrieve
from rag.synthesizer import synthesize

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


def query(question: str, top_k: int = 8, topics: list[str] = None,
          platforms: list[str] = None, tags: list[str] = None) -> str:
    """
    Run a question against the Sabrina RAG system and return a synthesized answer.
    platforms and tags are appended to the query string to steer retrieval.
    """
    # Augment the query with platforms/tags so the embedding steers toward relevant chunks
    augmented = question
    if platforms:
        augmented += " " + " ".join(platforms)
    if tags:
        augmented += " " + " ".join(t.replace("-", " ") for t in tags)

    chunks = retrieve(query=augmented, top_k=top_k, topics=topics)

    if not chunks:
        return "No relevant content found for your query. Try rephrasing or broadening the question."

    return synthesize(query=question, chunks=chunks)


def save_result(question: str, answer: str) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", question.lower())[:60].strip("-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{slug}.md"
    path = os.path.join(RESULTS_DIR, filename)
    with open(path, "w") as f:
        f.write(f"# {question}\n\n")
        f.write(answer)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Sabrina RAG system")
    parser.add_argument("question",              help="Question to ask")
    parser.add_argument("--top-k",    type=int,  default=8,    help="Number of chunks to retrieve")
    parser.add_argument("--topics",   nargs="*", default=None, help="Filter chunks by topic")
    parser.add_argument("--platforms",nargs="*", default=None, help="Platform context (e.g. tiktok instagram)")
    parser.add_argument("--tags",     nargs="*", default=None, help="Tag context (e.g. short-form-video hooks)")
    parser.add_argument("--save",     action="store_true",     help="Save answer to results/ directory")
    args = parser.parse_args()

    print(f"\nQuery: {args.question}\n")

    answer = query(
        args.question,
        top_k=args.top_k,
        topics=args.topics,
        platforms=args.platforms,
        tags=args.tags,
    )

    print(answer)

    if args.save:
        path = save_result(args.question, answer)
        print(f"\n[Saved → {path}]")
