import json
import os
from agents.base_agent import BaseAgent

try:
    import instaloader
    _HAS_INSTALOADER = True
except ImportError:
    _HAS_INSTALOADER = False

try:
    from googleapiclient.discovery import build as yt_build
    _HAS_YT = True
except ImportError:
    _HAS_YT = False


class AudienceIntelligenceAgent(BaseAgent):
    MAX_PROFILES = 200

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loader = instaloader.Instaloader() if _HAS_INSTALOADER else None
        self._yt_service = None

    def _fetch_instagram_bio(self, username: str) -> str:
        if not self._loader:
            return ""
        try:
            profile = instaloader.Profile.from_username(self._loader.context, username)
            return profile.biography or ""
        except Exception as e:
            print(f"[AudienceAgent] Could not fetch Instagram bio for {username}: {e}")
            return ""

    def _fetch_youtube_bio(self, channel_id: str) -> str:
        if not self._yt_service:
            api_key = os.environ.get("YOUTUBE_API_KEY")
            if not api_key:
                return ""
            self._yt_service = yt_build("youtube", "v3", developerKey=api_key)
        try:
            resp = self._yt_service.channels().list(part="snippet", id=channel_id).execute()
            items = resp.get("items", [])
            return items[0]["snippet"].get("description", "") if items else ""
        except Exception as e:
            print(f"[AudienceAgent] Could not fetch YouTube bio for {channel_id}: {e}")
            return ""

    def run(self, content_items: list[dict]) -> dict:
        print("[AudienceIntelligenceAgent] Extracting unique commenters")
        seen = {}
        for item in content_items:
            platform = item.get("platform", "")
            post_id = item.get("id", "")
            for comment in item.get("comments", []):
                author = comment.get("author", "")
                if not author:
                    continue
                if author in seen:
                    seen[author]["comments"].append({"text": comment.get("text", ""), "post_id": post_id})
                else:
                    seen[author] = {
                        "username": author,
                        "platform": platform,
                        "bio": "",
                        "comments": [{"text": comment.get("text", ""), "post_id": post_id}]
                    }

        print(f"[AudienceIntelligenceAgent] Found {len(seen)} unique commenters, fetching up to {self.MAX_PROFILES} bios")
        profiles = []
        for i, (username, data) in enumerate(seen.items()):
            if i >= self.MAX_PROFILES:
                break
            if data["platform"] == "instagram":
                data["bio"] = self._fetch_instagram_bio(username)
            elif data["platform"] == "youtube":
                data["bio"] = self._fetch_youtube_bio(username)
            profiles.append(data)

        system_prompt = self.load_prompt("audience_intelligence")
        message = f"""Classify these commenter profiles and flag intent signals:
{json.dumps(profiles, indent=2)}"""

        result = self.call_claude(system=system_prompt, user_message=message, max_tokens=4096)
        return result
