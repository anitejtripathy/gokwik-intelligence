import json
import shutil
from pathlib import Path


AGENT_FILES = [
    "agency_context.json",
    "content_themes.json",
    "audience_profile.json",
    "gokwik_value_map.json",
    "engagement_stats.json",
]


class SiteGenerator:
    def __init__(
        self,
        agent_output_dir: str = "data/normalized",
        site_data_dir: str = "site/data",
    ):
        self.agent_output_dir = Path(agent_output_dir)
        self.site_data_dir = Path(site_data_dir)

    def generate(self):
        self.site_data_dir.mkdir(parents=True, exist_ok=True)
        for filename in AGENT_FILES:
            src = self.agent_output_dir / filename
            dst = self.site_data_dir / filename
            if src.exists():
                shutil.copy2(src, dst)
                print(f"[SiteGenerator] Copied {filename} to site/data/")
            else:
                print(f"[SiteGenerator] WARNING: {src} not found — skipping")
        print("[SiteGenerator] Site data ready. Open site/index.html or deploy to GitHub Pages.")
