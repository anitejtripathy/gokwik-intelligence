import json
from pathlib import Path
from unittest.mock import MagicMock
from report_generator import ReportGenerator

STUB_INPUTS = {
    "agency_context": {"business_model_summary": "Creator agency", "revenue_streams": [], "validated_success_stories": [], "content_strategy_playbook": [], "what_gokwik_gets": []},
    "content_themes": {"items": [], "theme_frequency": {}, "top_posts_per_theme": {}},
    "audience_profile": {"total_unique_commenters": 0, "d2c_brand_count": 5, "merchant_individual_count": 3, "top_d2c_engagers": [], "intent_signal_comments": []},
    "gokwik_value_map": {"benefits": [], "overall_strategic_assessment": "Significant risk"},
    "engagement_stats": {"total_post_count": 10, "total_estimated_reach": 100000, "by_platform": {}, "by_theme": {}, "top_10_posts": []},
}

def test_report_generator_creates_brief(tmp_path):
    gen = ReportGenerator(output_dir=str(tmp_path), prompts_dir="prompts")
    gen.client = MagicMock()
    gen.client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="## Executive Summary\n- GoKwik is using a creator agency")]
    )
    gen.generate_brief(**STUB_INPUTS)
    brief = (tmp_path / "brief.md").read_text()
    assert "Executive Summary" in brief

def test_report_generator_creates_data_tables(tmp_path):
    gen = ReportGenerator(output_dir=str(tmp_path), prompts_dir="prompts")
    gen.generate_data_tables(**STUB_INPUTS)
    tables = (tmp_path / "data-tables.md").read_text()
    assert "GoKwik Value Map" in tables
    assert "Engagement Stats" in tables
