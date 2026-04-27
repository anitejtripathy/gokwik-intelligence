import json
from pathlib import Path
from site_generator import SiteGenerator

def test_site_generator_copies_jsons(tmp_path):
    agent_outputs = tmp_path / "agent_outputs"
    agent_outputs.mkdir()
    (agent_outputs / "agency_context.json").write_text(json.dumps({"test": 1}))
    (agent_outputs / "content_themes.json").write_text(json.dumps({"test": 2}))
    (agent_outputs / "audience_profile.json").write_text(json.dumps({"test": 3}))
    (agent_outputs / "gokwik_value_map.json").write_text(json.dumps({"test": 4}))
    (agent_outputs / "engagement_stats.json").write_text(json.dumps({"test": 5}))

    site_data_dir = tmp_path / "site" / "data"
    gen = SiteGenerator(agent_output_dir=str(agent_outputs), site_data_dir=str(site_data_dir))
    gen.generate()

    assert (site_data_dir / "agency_context.json").exists()
    assert (site_data_dir / "engagement_stats.json").exists()
    data = json.loads((site_data_dir / "agency_context.json").read_text())
    assert data["test"] == 1
