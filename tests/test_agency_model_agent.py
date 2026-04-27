import json
from unittest.mock import MagicMock, patch
from agents.agency_model_agent import AgencyModelAgent


MOCK_CONTEXT = {
    "business_model_summary": "GrowKwik operates as a creator-led growth agency",
    "revenue_streams": [
        {"type": "brand_deal", "description": "Paid integrations", "confidence": "high", "evidence": "stated in video"}
    ],
    "content_strategy_playbook": ["Post 3 reels per week"],
    "validated_success_stories": [
        {"brand": "Zoho", "outcome": "3x growth", "mechanism": "creator content", "source": "https://example.com"}
    ],
    "what_gokwik_gets": ["App installs via CTA", "Merchant leads"]
}


def test_agency_model_agent_returns_valid_schema():
    agent = AgencyModelAgent(prompts_dir="prompts")
    agent.client = MagicMock()
    agent.client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(MOCK_CONTEXT))]
    )
    with patch("agents.agency_model_agent.DDGS") as mock_ddgs:
        mock_ddgs.return_value.__enter__.return_value.text.return_value = [
            {"title": "Zoho Case Study", "body": "Zoho grew 3x", "href": "https://example.com"}
        ]
        result = agent.run(transcripts=["This is a video about GoKwik..."], varun_maya_transcript="Varun explains the model")
    assert "business_model_summary" in result
    assert "revenue_streams" in result
    assert isinstance(result["revenue_streams"], list)
