import json
import os
import re
from pathlib import Path
import anthropic


class BaseAgent:
    MODEL = "claude-sonnet-4-6"

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def load_prompt(self, name: str) -> str:
        path = self.prompts_dir / f"{name}.md"
        return path.read_text()

    def call_claude(self, system: str, user_message: str, max_tokens: int = 4096) -> dict:
        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}]
        )
        raw = response.content[0].text
        return self._parse_json(raw)

    def _parse_json(self, text: str) -> dict:
        # Strip markdown code fences if present
        match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
        if match:
            text = match.group(1)
        return json.loads(text.strip())
