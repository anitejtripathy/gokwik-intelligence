import json
from unittest.mock import MagicMock
from agents.content_theme_agent import ContentThemeAgent

MOCK_OUTPUT = {
    "items": [
        {"id": "vid1", "platform": "youtube", "themes": ["gokwik_feature_push"], "primary_theme": "gokwik_feature_push", "theme_evidence": "install GoKwik now"}
    ],
    "theme_frequency": {"brand_integration": 0, "gokwik_feature_push": 1, "thought_leadership": 0, "merchant_testimonial": 0, "lead_gen": 0, "community_building": 0},
    "top_posts_per_theme": {"gokwik_feature_push": [{"id": "vid1", "url": "https://youtube.com/watch?v=vid1", "engagement_rate": 0.05}],
                            "brand_integration": [], "thought_leadership": [], "merchant_testimonial": [], "lead_gen": [], "community_building": []}
}

def test_content_theme_agent_run():
    agent = ContentThemeAgent(prompts_dir="prompts")
    agent.client = MagicMock()
    agent.client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(MOCK_OUTPUT))]
    )
    content_items = [{"id": "vid1", "platform": "youtube", "type": "video", "transcript": "install GoKwik now", "text": "", "engagement": {"engagement_rate": 0.05}, "url": "https://youtube.com/watch?v=vid1"}]
    agency_context = {"business_model_summary": "creator agency"}
    result = agent.run(content_items=content_items, agency_context=agency_context)
    assert result["items"][0]["primary_theme"] == "gokwik_feature_push"
    assert result["theme_frequency"]["gokwik_feature_push"] == 1
