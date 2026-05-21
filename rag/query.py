#!/usr/bin/env python3
"""
Main query interface for the Sabrina RAG system.

Usage:
  python -m rag.query "How does Sabrina approach LinkedIn content?"
  python -m rag.query "What AI tools does she recommend?" --top-k 12
  python -m rag.query "prompt engineering tips" --topics "prompt engineering" "ChatGPT"
"""

import argparse
from dotenv import load_dotenv

load_dotenv()

from rag.retriever import retrieve
from rag.synthesizer import synthesize


def query(question: str, top_k: int = 8, topics: list[str] = None) -> str:
    """
    Run a question against the Sabrina RAG system and return a synthesized answer.
    """
    chunks = retrieve(query=question, top_k=top_k, topics=topics)

    if not chunks:
        return "No relevant content found for your query. Try rephrasing or broadening the question."

    return synthesize(query=question, chunks=chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Sabrina RAG system")
    parser.add_argument("question",           help="Question to ask")
    parser.add_argument("--top-k",  type=int, default=8,   help="Number of chunks to retrieve")
    parser.add_argument("--topics", nargs="*", default=None, help="Filter by topics")
    args = parser.parse_args()

    print(f"\nQuery: {args.question}")
    if args.topics:
        print(f"Topic filter: {args.topics}")
    print("\nRetrieving...\n")

    answer = query(args.question, top_k=args.top_k, topics=args.topics)
    print(answer)
