import json
import os
import re
from pathlib import Path
from anthropic import AnthropicVertex


class BaseAgent:
    MODEL = "claude-sonnet-4-6"

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.client = AnthropicVertex(
            project_id=os.environ["ANTHROPIC_VERTEX_PROJECT_ID"],
            region=os.environ.get("CLOUD_ML_REGION", "us-east5"),
        )

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
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"[BaseAgent] Failed to parse JSON response: {e}")
            print(f"[BaseAgent] Raw response (first 500 chars): {text[:500]}")
            raise
