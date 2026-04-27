import json
from duckduckgo_search import DDGS
from agents.base_agent import BaseAgent


class AgencyModelAgent(BaseAgent):
    def run(self, transcripts: list[str], varun_maya_transcript: str) -> dict:
        print("[AgencyModelAgent] Phase A: Transcript analysis")
        system_prompt = self.load_prompt("agency_model")

        all_transcripts = f"=== VARUN MAYA EXPOSE VIDEO ===\n{varun_maya_transcript}\n\n"
        all_transcripts += "\n\n".join(
            f"=== GROWKWIK VIDEO {i+1} ===\n{t}" for i, t in enumerate(transcripts)
        )

        phase_a_message = f"""Analyze these transcripts and return Phase A hypotheses as JSON.

TRANSCRIPTS:
{all_transcripts[:50000]}"""

        hypotheses = self.call_claude(system=system_prompt, user_message=phase_a_message, max_tokens=4096)

        print("[AgencyModelAgent] Phase B: Web validation")
        search_results = self._web_search(hypotheses)

        phase_b_message = f"""You previously analyzed transcripts and produced these hypotheses:
{json.dumps(hypotheses, indent=2)}

Here are web search results to validate them:
{json.dumps(search_results, indent=2)}

Revise or confirm your hypotheses based on the search results. Return the final validated JSON schema."""

        validated = self.call_claude(system=system_prompt, user_message=phase_b_message, max_tokens=4096)
        return validated

    def _web_search(self, hypotheses: dict) -> list[dict]:
        queries = [
            "Varun Maya creator agency India GoKwik",
            "GrowKwik agency D2C ecommerce India",
            "GoKwik creator marketing strategy",
            "Zoho creator agency growth case study India",
        ]
        for stream in hypotheses.get("revenue_streams", [])[:2]:
            queries.append(f"creator agency {stream.get('type', '')} India D2C ecommerce")

        results = []
        with DDGS() as ddgs:
            for query in queries[:5]:
                try:
                    hits = list(ddgs.text(query, max_results=3))
                    results.append({"query": query, "results": hits})
                except Exception as e:
                    results.append({"query": query, "results": [], "error": str(e)})
        return results
