import json
from agents.base_agent import BaseAgent


class GoKwikBenefitsAgent(BaseAgent):
    def run(self, agency_context: dict, content_themes: dict, audience_profile: dict) -> dict:
        print("[GoKwikBenefitsAgent] Mapping GoKwik benefits")
        system_prompt = self.load_prompt("gokwik_benefits")
        message = f"""agency_context:
{json.dumps(agency_context, indent=2)}

content_themes:
{json.dumps(content_themes, indent=2)}

audience_profile:
{json.dumps(audience_profile, indent=2)}"""

        return self.call_claude(system=system_prompt, user_message=message, max_tokens=4096)
