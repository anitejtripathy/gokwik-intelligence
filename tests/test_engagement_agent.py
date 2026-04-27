from agents.engagement_agent import EngagementAgent

ITEMS = [
    {"id": "v1", "platform": "youtube", "type": "video", "published_at": "2024-01-01T00:00:00Z",
     "url": "https://youtube.com/watch?v=v1",
     "engagement": {"views": 10000, "likes": 500, "comments": 80, "engagement_rate": 0.058}},
    {"id": "v2", "platform": "youtube", "type": "video", "published_at": "2024-02-01T00:00:00Z",
     "url": "https://youtube.com/watch?v=v2",
     "engagement": {"views": 5000, "likes": 200, "comments": 30, "engagement_rate": 0.046}},
    {"id": "ig1", "platform": "instagram", "type": "reel", "published_at": "2024-03-01T00:00:00Z",
     "url": "https://instagram.com/p/ig1/",
     "engagement": {"views": 20000, "likes": 1500, "comments": 200, "engagement_rate": 0.085}},
]
THEMES = {
    "items": [
        {"id": "v1", "primary_theme": "gokwik_feature_push"},
        {"id": "v2", "primary_theme": "thought_leadership"},
        {"id": "ig1", "primary_theme": "brand_integration"},
    ]
}

def test_compute_top_posts():
    agent = EngagementAgent()
    stats = agent.run(content_items=ITEMS, content_themes=THEMES)
    assert stats["top_10_posts"][0]["id"] == "ig1"  # highest engagement rate

def test_compute_avg_by_platform():
    agent = EngagementAgent()
    stats = agent.run(content_items=ITEMS, content_themes=THEMES)
    assert stats["by_platform"]["youtube"]["avg_views"] == 7500
    assert stats["by_platform"]["instagram"]["avg_engagement_rate"] == 0.085

def test_total_estimated_reach():
    agent = EngagementAgent()
    stats = agent.run(content_items=ITEMS, content_themes=THEMES)
    assert stats["total_estimated_reach"] == 35000
