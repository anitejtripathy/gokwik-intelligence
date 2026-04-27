import json
from agents.base_agent import BaseAgent


class ContentThemeAgent(BaseAgent):
    CHUNK_SIZE = 20  # items per Claude call to avoid token limits

    def run(self, content_items: list[dict], agency_context: dict) -> dict:
        print(f"[ContentThemeAgent] Classifying {len(content_items)} items")
        system_prompt = self.load_prompt("content_theme")
        all_classified = []

        for i in range(0, len(content_items), self.CHUNK_SIZE):
            chunk = content_items[i:i + self.CHUNK_SIZE]
            slim_chunk = [
                {
                    "id": item.get("id", ""),
                    "platform": item.get("platform", ""),
                    "type": item.get("type", ""),
                    "text": (item.get("transcript") or item.get("text", ""))[:3000],
                    "engagement": item.get("engagement", {}),
                    "url": item.get("url", ""),
                }
                for item in chunk
            ]
            message = f"""Agency context (for reference):
{json.dumps(agency_context, indent=2)}

Content items to classify:
{json.dumps(slim_chunk, indent=2)}"""

            result = self.call_claude(system=system_prompt, user_message=message, max_tokens=4096)
            all_classified.extend(result.get("items", []))

        theme_keys = ["brand_integration", "gokwik_feature_push", "thought_leadership",
                      "merchant_testimonial", "lead_gen", "community_building"]
        freq = {k: 0 for k in theme_keys}
        top = {k: [] for k in theme_keys}

        for item in all_classified:
            for theme in item.get("themes", []):
                if theme in freq:
                    freq[theme] += 1
            pt = item.get("primary_theme")
            if pt in top:
                source_item = next((c for c in content_items if c.get("id") == item.get("id")), {})
                top[pt].append({
                    "id": item.get("id", ""),
                    "url": source_item.get("url", ""),
                    "engagement_rate": source_item.get("engagement", {}).get("engagement_rate", 0),
                })

        return {"items": all_classified, "theme_frequency": freq, "top_posts_per_theme": top}
