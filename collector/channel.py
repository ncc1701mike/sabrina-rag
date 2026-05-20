from googleapiclient.discovery import build
from dotenv import load_dotenv
import os

load_dotenv()

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def get_channel_id(handle: str) -> str:
    """Convert a @handle to a channel ID."""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    response = youtube.search().list(
        q=handle,
        type="channel",
        part="id,snippet",
        maxResults=1
    ).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"Channel not found for handle: {handle}")
    return items[0]["id"]["channelId"]

def get_all_video_ids(channel_id: str) -> list[dict]:
    """
    Return list of dicts with video_id + basic metadata
    for every video on the channel.
    Uses pagination to get all videos.
    """
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    videos = []
    next_page_token = None

    print(f"Fetching video list for channel: {channel_id}")

    while True:
        response = youtube.search().list(
            channelId=channel_id,
            type="video",
            part="id,snippet",
            maxResults=50,
            order="date",
            pageToken=next_page_token
        ).execute()

        for item in response.get("items", []):
            videos.append({
                "video_id":      item["id"]["videoId"],
                "title":         item["snippet"]["title"],
                "published_at":  item["snippet"]["publishedAt"],
                "thumbnail_url": item["snippet"]["thumbnails"].get("high", {}).get("url"),
                "channel_id":    item["snippet"]["channelId"],
                "channel_title": item["snippet"]["channelTitle"],
            })

        next_page_token = response.get("nextPageToken")
        print(f"  Fetched {len(videos)} videos so far...")
        if not next_page_token:
            break

    print(f"Total videos found: {len(videos)}")
    return videos

def get_video_details(video_ids: list[str]) -> dict:
    """
    Fetch detailed metadata for a batch of video IDs.
    Returns dict keyed by video_id.
    YouTube API allows up to 50 IDs per request.
    """
    import re
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    details = {}

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i+50]
        response = youtube.videos().list(
            id=",".join(batch),
            part="contentDetails,statistics,snippet"
        ).execute()

        for item in response.get("items", []):
            vid = item["id"]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})

            duration_str = content.get("duration", "PT0S")
            match = re.match(
                r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',
                duration_str
            )
            if match:
                h = int(match.group(1) or 0)
                m = int(match.group(2) or 0)
                s = int(match.group(3) or 0)
                duration_seconds = h * 3600 + m * 60 + s
            else:
                duration_seconds = 0

            details[vid] = {
                "duration_seconds": duration_seconds,
                "view_count":       int(stats.get("viewCount", 0)),
                "like_count":       int(stats.get("likeCount", 0)),
                "description":      snippet.get("description", ""),
                "tags":             snippet.get("tags", []),
            }

    return details
