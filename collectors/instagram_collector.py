import json
import re
import ssl
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import instaloader
from collectors.schema import normalize_instagram_post, ContentItem

# Whisper is loaded lazily to avoid slow startup
_whisper_model = None


def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("[Whisper] Loading model (first reel — this takes ~30s)")
        _whisper_model = whisper.load_model("base")
    return _whisper_model


class InstagramCollector:
    def __init__(self, username: str, output_dir: str = "data/raw/instagram"):
        self.username = username
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "comments").mkdir(exist_ok=True)
        (self.output_dir / "transcripts").mkdir(exist_ok=True)
        # Disable SSL verification to handle Zscaler cert on corporate networks
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        self.loader = instaloader.Instaloader()
        self.loader.context._session.verify = False

    def _classify_post_type(self, is_video: bool, media_count: int) -> str:
        if is_video:
            return "reel"
        if media_count > 1:
            return "carousel"
        return "image"

    def _extract_hashtags(self, caption: str) -> list[str]:
        return re.findall(r"#(\w+)", caption or "")

    def _build_post_dict(self, post) -> dict:
        caption = post.caption or ""
        is_video = post.is_video
        media_count = getattr(post, "mediacount", 1)
        typename = "GraphVideo" if is_video else ("GraphSidecar" if media_count > 1 else "GraphImage")
        return {
            "shortcode": post.shortcode,
            "caption": caption,
            "typename": typename,
            "views": post.video_view_count if is_video else 0,
            "likes": post.likes,
            "comments_count": post.comments,
            "timestamp": post.date_utc.isoformat() + "Z",
            "hashtags": self._extract_hashtags(caption),
            "url": post.url,
        }

    def _fetch_comments(self, post, max_comments: int = 100) -> list[dict]:
        comments = []
        try:
            for i, comment in enumerate(post.get_comments()):
                if i >= max_comments:
                    break
                comments.append({
                    "author": comment.owner.username,
                    "text": comment.text,
                    "likes": getattr(comment, "likes_count", 0)
                })
        except Exception as e:
            print(f"[Instagram] Error fetching comments for {post.shortcode}: {e}")
        return comments

    def _transcribe_reel(self, post) -> Optional[str]:
        """Download reel audio via yt-dlp and transcribe with Whisper."""
        url = f"https://www.instagram.com/p/{post.shortcode}/"
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = f"{tmp}/audio.mp3"
            result = subprocess.run(
                ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_path, url],
                capture_output=True, timeout=120
            )
            if result.returncode != 0:
                print(f"[Instagram] yt-dlp failed for {post.shortcode}: {result.stderr.decode()[:200]}")
                return None
            try:
                model = _get_whisper_model()
                transcription = model.transcribe(audio_path)
                return transcription["text"].strip()
            except Exception as e:
                print(f"[Instagram] Whisper transcription failed for {post.shortcode}: {e}")
                return None

    def _fetch_profile_meta(self, profile) -> dict:
        meta = {
            "username": profile.username,
            "followers": profile.followers,
            "bio": profile.biography,
            "post_count": profile.mediacount,
        }
        path = self.output_dir / "profile_meta.json"
        path.write_text(json.dumps(meta, indent=2))
        return meta

    def collect_all(self) -> list[ContentItem]:
        print(f"[Instagram] Loading profile: {self.username}")
        profile = instaloader.Profile.from_username(self.loader.context, self.username)
        self._fetch_profile_meta(profile)

        all_posts_raw = []
        items = []

        for post in profile.get_posts():
            shortcode = post.shortcode
            print(f"[Instagram] Processing post {shortcode} ({post.date_utc.date()})")

            post_dict = self._build_post_dict(post)
            comments = self._fetch_comments(post)

            (self.output_dir / "comments" / f"{shortcode}.json").write_text(
                json.dumps(comments, indent=2)
            )

            # Transcribe reels via Whisper; use caption for image/carousel
            transcript = None
            if post_dict["typename"] == "GraphVideo":
                transcript = self._transcribe_reel(post)
                if transcript:
                    (self.output_dir / "transcripts" / f"{shortcode}.txt").write_text(transcript)

            all_posts_raw.append(post_dict)
            item = normalize_instagram_post(post_dict, comments, transcript)
            items.append(item)

        (self.output_dir / "posts.json").write_text(json.dumps(all_posts_raw, indent=2))
        return items
