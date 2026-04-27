import json
from pathlib import Path
from agents.base_agent import BaseAgent


class ReportGenerator(BaseAgent):
    def __init__(self, output_dir: str = "output", **kwargs):
        super().__init__(**kwargs)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_brief(self, agency_context, content_themes, audience_profile, gokwik_value_map, engagement_stats) -> str:
        print("[ReportGenerator] Generating leadership brief")
        system_prompt = self.load_prompt("report_generator")
        message = f"""agency_context: {json.dumps(agency_context, indent=2)}

content_themes summary:
- Total items: {len(content_themes.get('items', []))}
- Theme frequency: {json.dumps(content_themes.get('theme_frequency', {}), indent=2)}
- Top posts per theme (first 3 per theme): {json.dumps({k: v[:3] for k, v in content_themes.get('top_posts_per_theme', {}).items()}, indent=2)}

audience_profile: {json.dumps(audience_profile, indent=2)}

gokwik_value_map: {json.dumps(gokwik_value_map, indent=2)}

engagement_stats: {json.dumps(engagement_stats, indent=2)}"""

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        )
        brief = response.content[0].text
        path = self.output_dir / "brief.md"
        path.write_text(brief)
        print(f"[ReportGenerator] Brief saved to {path}")
        return brief

    def generate_data_tables(self, agency_context, content_themes, audience_profile, gokwik_value_map, engagement_stats) -> str:
        lines = ["# GoKwik Social Intelligence — Data Tables\n"]

        lines.append("## Agency Business Model\n")
        lines.append("| Revenue Stream | Description | Confidence | Evidence |")
        lines.append("|---|---|---|---|")
        for rs in agency_context.get("revenue_streams", []):
            lines.append(f"| {rs.get('type','')} | {rs.get('description','')} | {rs.get('confidence','')} | {rs.get('evidence','')} |")
        lines.append("")

        lines.append("## GoKwik Value Map\n")
        lines.append("| Benefit Type | Description | Estimated Scale | Frequency |")
        lines.append("|---|---|---|---|")
        for b in gokwik_value_map.get("benefits", []):
            lines.append(f"| {b.get('type','')} | {b.get('description','')} | {b.get('estimated_scale','')} | {b.get('frequency','')} |")
        lines.append("")

        lines.append("## D2C Audience Summary\n")
        lines.append(f"- Total unique commenters: {audience_profile.get('total_unique_commenters', 0)}")
        lines.append(f"- D2C brands: {audience_profile.get('d2c_brand_count', 0)}")
        lines.append(f"- Merchant individuals: {audience_profile.get('merchant_individual_count', 0)}")
        lines.append("\n### Top D2C Engagers\n")
        lines.append("| Username | Platform | Bio | Comment | Intent Signal |")
        lines.append("|---|---|---|---|---|")
        for e in audience_profile.get("top_d2c_engagers", [])[:20]:
            lines.append(f"| {e.get('username','')} | {e.get('platform','')} | {e.get('bio','')[:80]} | {e.get('comment','')[:100]} | {e.get('intent_signal','')} |")
        lines.append("")

        lines.append("## Engagement Stats\n")
        lines.append(f"- Total posts: {engagement_stats.get('total_post_count', 0)}")
        lines.append(f"- Total estimated reach: {engagement_stats.get('total_estimated_reach', 0):,}")
        lines.append("\n### Top 10 Posts by Engagement Rate\n")
        lines.append("| Platform | Theme | Engagement Rate | Views | URL |")
        lines.append("|---|---|---|---|---|")
        for p in engagement_stats.get("top_10_posts", []):
            lines.append(f"| {p.get('platform','')} | {p.get('theme','')} | {p.get('engagement_rate',0):.2%} | {p.get('views',0):,} | {p.get('url','')} |")

        content = "\n".join(lines)
        path = self.output_dir / "data-tables.md"
        path.write_text(content)
        print(f"[ReportGenerator] Data tables saved to {path}")
        return content
