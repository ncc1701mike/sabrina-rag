# sabrina-rag

Collects YouTube transcripts and stores them in Supabase for RAG pipelines.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in .env with your keys
```

## Usage

```bash
python collector/run.py
```

## Structure

- `collector/channel.py` — fetches all video IDs from a YouTube channel
- `collector/transcripts.py` — downloads transcripts per video
- `collector/storage.py` — writes transcript data to Supabase
- `collector/run.py` — orchestrates the full collection run
