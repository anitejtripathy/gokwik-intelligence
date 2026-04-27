import json
from collectors.schema import ContentItem, Comment, Engagement, normalize_youtube_video, normalize_instagram_post

def test_content_item_to_dict_roundtrip():
    item = ContentItem(
        id="vid123",
        platform="youtube",
        type="video",
        title="Test Video",
        text="Test description",
        transcript="Hello world",
        engagement=Engagement(views=1000, likes=50, comments=10, engagement_rate=0.06),
        published_at="2024-01-15T10:00:00Z",
        comments=[Comment(author="user1", text="great video", likes=5)],
        tags=["ecommerce", "D2C"],
        url="https://youtube.com/watch?v=vid123"
    )
    d = item.to_dict()
    assert d["id"] == "vid123"
    assert d["platform"] == "youtube"
    assert d["engagement"]["views"] == 1000
    assert d["comments"][0]["author"] == "user1"

def test_normalize_youtube_video():
    raw_video = {
        "id": "vid123",
        "snippet": {
            "title": "GoKwik Demo",
            "description": "Watch this demo",
            "publishedAt": "2024-01-15T10:00:00Z",
            "tags": ["gokwik"]
        },
        "statistics": {
            "viewCount": "5000",
            "likeCount": "200",
            "commentCount": "30"
        }
    }
    raw_comments = [{"author": "shopowner", "text": "How do I install?", "likes": 3}]
    transcript = "Welcome to the GoKwik demo"

    item = normalize_youtube_video(raw_video, raw_comments, transcript)
    assert item.platform == "youtube"
    assert item.type == "video"
    assert item.title == "GoKwik Demo"
    assert item.engagement.views == 5000
    assert item.engagement.engagement_rate == round((200 + 30) / 5000, 4)
    assert item.transcript == "Welcome to the GoKwik demo"

def test_normalize_instagram_post_reel():
    raw_post = {
        "shortcode": "ABC123",
        "caption": "Check out this reel",
        "typename": "GraphVideo",
        "likes": 300,
        "comments_count": 20,
        "timestamp": "2024-02-10T08:00:00Z",
        "hashtags": ["d2c", "ecommerce"],
        "url": "https://instagram.com/p/ABC123/"
    }
    raw_comments = [{"author": "brand_founder", "text": "Interested!", "likes": 1}]
    transcript = "This is the spoken content"

    item = normalize_instagram_post(raw_post, raw_comments, transcript)
    assert item.platform == "instagram"
    assert item.type == "reel"
    assert item.transcript == "This is the spoken content"
    assert item.engagement.likes == 300
