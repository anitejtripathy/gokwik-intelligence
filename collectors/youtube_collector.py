import json
import os
from pathlib import Path
from typing import Optional
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from collectors.schema import normalize_youtube_video, ContentItem


class YouTubeCollector:
    def __init__(self, service=None, output_dir: str = "data/raw/youtube", api_key: str = None):
        if service:
            self.service = service
        else:
            self.service = build("youtube", "v3", developerKey=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "comments").mkdir(exist_ok=True)
        (self.output_dir / "transcripts").mkdir(exist_ok=True)

    def fetch_channel_meta(self, channel_id: str) -> dict:
        resp = self.service.channels().list(
            part="snippet,statistics", id=channel_id
        ).execute()
        meta = resp["items"][0]
        path = self.output_dir / "channel_meta.json"
        path.write_text(json.dumps(meta, indent=2))
        return meta

    def fetch_all_video_ids(self, channel_id: str) -> list[str]:
        ids = []
        page_token = None
        while True:
            params = dict(part="id", channelId=channel_id, maxResults=50, type="video")
            if page_token:
                params["pageToken"] = page_token
            resp = self.service.search().list(**params).execute()
            ids += [item["id"]["videoId"] for item in resp.get("items", [])]
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        return ids

    def fetch_video_details(self, video_ids: list[str]) -> list[dict]:
        all_videos = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            resp = self.service.videos().list(
                part="snippet,statistics", id=",".join(batch)
            ).execute()
            all_videos.extend(resp.get("items", []))
        path = self.output_dir / "videos.json"
        path.write_text(json.dumps(all_videos, indent=2))
        return all_videos

    def fetch_comments(self, video_id: str, max_comments: int = 100) -> list[dict]:
        comments = []
        page_token = None
        while len(comments) < max_comments:
            params = dict(
                part="snippet", videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                order="relevance"
            )
            if page_token:
                params["pageToken"] = page_token
            try:
                resp = self.service.commentThreads().list(**params).execute()
            except Exception:
                break
            for item in resp.get("items", []):
                s = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": s["authorDisplayName"],
                    "text": s["textDisplay"],
                    "likes": s.get("likeCount", 0)
                })
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
        path = self.output_dir / "comments" / f"{video_id}.json"
        path.write_text(json.dumps(comments, indent=2))
        return comments

    def fetch_transcript(self, video_id: str) -> Optional[str]:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "hi"])
            text = " ".join(t["text"] for t in transcript_list)
            path = self.output_dir / "transcripts" / f"{video_id}.txt"
            path.write_text(text)
            return text
        except (NoTranscriptFound, TranscriptsDisabled):
            return None

    def collect_all(self, channel_id: str) -> list[ContentItem]:
        print(f"[YouTube] Fetching channel meta for {channel_id}")
        self.fetch_channel_meta(channel_id)

        print("[YouTube] Fetching all video IDs")
        video_ids = self.fetch_all_video_ids(channel_id)
        print(f"[YouTube] Found {len(video_ids)} videos")

        videos = self.fetch_video_details(video_ids)
        items = []
        for video in videos:
            vid_id = video.get("id", "")
            print(f"[YouTube] Processing {vid_id}: {video['snippet']['title'][:50]}")
            comments = self.fetch_comments(vid_id)
            transcript = self.fetch_transcript(vid_id)
            item = normalize_youtube_video(video, comments, transcript)
            items.append(item)
        return items
