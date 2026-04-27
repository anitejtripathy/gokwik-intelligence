import json
from unittest.mock import MagicMock, patch
from agents.audience_intelligence_agent import AudienceIntelligenceAgent

MOCK_OUTPUT = {
    "total_unique_commenters": 2,
    "d2c_brand_count": 1,
    "merchant_individual_count": 1,
    "consumer_count": 0,
    "unknown_count": 0,
    "top_d2c_engagers": [
        {"username": "coolbrand", "platform": "instagram", "bio": "Official brand store", "comment": "Interested!", "post_id": "ABC", "intent_signal": "interest"}
    ],
    "intent_signal_comments": [
        {"username": "coolbrand", "comment": "Interested!", "post_id": "ABC", "signal_type": "interest"}
    ]
}

def test_audience_agent_run():
    agent = AudienceIntelligenceAgent(prompts_dir="prompts")
    agent.client = MagicMock()
    agent.client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(MOCK_OUTPUT))]
    )
    content_items = [
        {
            "id": "ABC", "platform": "instagram",
            "comments": [
                {"author": "coolbrand", "text": "Interested!", "likes": 2},
                {"author": "founder_guy", "text": "How much does it cost?", "likes": 1}
            ]
        }
    ]
    with patch.object(agent, "_fetch_instagram_bio", return_value="Official brand store"):
        with patch.object(agent, "_fetch_youtube_bio", return_value="D2C founder"):
            result = agent.run(content_items=content_items)
    assert result["d2c_brand_count"] == 1
    assert len(result["intent_signal_comments"]) == 1
