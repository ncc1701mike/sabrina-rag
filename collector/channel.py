from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import re

load_dotenv()

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

def get_youtube():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_channel_id(handle: str) -> str:
    """Convert a @handle to a channel ID."""
    youtube = get_youtube()
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

def get_uploads_playlist_id(channel_id: str) -> str:
    """
    Get the uploads playlist ID for a channel.
    Every YouTube channel has a hidden uploads playlist
    where ALL videos appear — no pagination limit.
    The uploads playlist ID is the channel ID with
    the second character changed from C to U.
    e.g. UCxxxxxx -> UUxxxxxx
    """
    youtube = get_youtube()
    response = youtube.channels().list(
        id=channel_id,
        part="contentDetails"
    ).execute()
    items = response.get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_all_video_ids(channel_id: str) -> list[dict]:
    """
    Return list of dicts with video_id + basic metadata
    for every video on the channel using the uploads playlist.
    No result cap — gets every single video.
    """
    youtube = get_youtube()

    uploads_playlist_id = get_uploads_playlist_id(channel_id)
    print(f"Uploads playlist ID: {uploads_playlist_id}")

    videos = []
    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet,contentDetails",
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            video_id = content.get("videoId") or snippet.get("resourceId", {}).get("videoId")
            if not video_id:
                continue
            videos.append({
                "video_id":      video_id,
                "title":         snippet.get("title", ""),
                "published_at":  snippet.get("publishedAt") or content.get("videoPublishedAt"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "channel_id":    snippet.get("channelId", ""),
                "channel_title": snippet.get("channelTitle", ""),
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
    youtube = get_youtube()
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
