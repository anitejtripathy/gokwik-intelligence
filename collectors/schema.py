from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Comment:
    author: str
    text: str
    likes: int = 0


@dataclass
class Engagement:
    views: int = 0
    likes: int = 0
    comments: int = 0
    engagement_rate: float = 0.0


@dataclass
class ContentItem:
    id: str
    platform: str        # "youtube" | "instagram"
    type: str            # "video" | "reel" | "image" | "carousel"
    title: Optional[str]
    text: str
    transcript: Optional[str]
    engagement: Engagement
    published_at: str    # ISO8601
    comments: list
    tags: list
    url: str

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_youtube_video(
    raw_video: dict,
    raw_comments: list[dict],
    transcript: Optional[str]
) -> ContentItem:
    stats = raw_video.get("statistics", {})
    views = int(stats.get("viewCount", 0))
    likes = int(stats.get("likeCount", 0))
    comments_count = int(stats.get("commentCount", 0))
    engagement_rate = round((likes + comments_count) / views, 4) if views > 0 else 0.0

    snippet = raw_video.get("snippet", {})
    video_id = raw_video.get("id", "")

    return ContentItem(
        id=video_id,
        platform="youtube",
        type="video",
        title=snippet.get("title"),
        text=snippet.get("description", ""),
        transcript=transcript,
        engagement=Engagement(
            views=views,
            likes=likes,
            comments=comments_count,
            engagement_rate=engagement_rate,
        ),
        published_at=snippet.get("publishedAt", ""),
        comments=[Comment(author=c.get("author", ""), text=c.get("text", ""), likes=c.get("likes", 0)) for c in raw_comments],
        tags=snippet.get("tags", []),
        url=f"https://youtube.com/watch?v={video_id}",
    )


def normalize_instagram_post(
    raw_post: dict,
    raw_comments: list[dict],
    transcript: Optional[str]
) -> ContentItem:
    typename = raw_post.get("typename", "GraphImage")
    type_map = {
        "GraphVideo": "reel",
        "GraphImage": "image",
        "GraphSidecar": "carousel",
    }
    post_type = type_map.get(typename, "image")

    likes = raw_post.get("likes", 0)
    comments_count = raw_post.get("comments_count", 0)
    views = raw_post.get("views", likes * 10 if post_type == "reel" else 0)
    engagement_rate = round((likes + comments_count) / views, 4) if views > 0 else 0.0

    caption = raw_post.get("caption", "") or ""
    effective_transcript = transcript if transcript else caption

    return ContentItem(
        id=raw_post.get("shortcode", ""),
        platform="instagram",
        type=post_type,
        title=None,
        text=caption,
        transcript=effective_transcript,
        engagement=Engagement(
            views=views,
            likes=likes,
            comments=comments_count,
            engagement_rate=engagement_rate,
        ),
        published_at=raw_post.get("timestamp", ""),
        comments=[Comment(author=c.get("author", ""), text=c.get("text", ""), likes=c.get("likes", 0)) for c in raw_comments],
        tags=raw_post.get("hashtags", []),
        url=raw_post.get("url", ""),
    )
