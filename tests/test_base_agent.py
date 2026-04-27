from unittest.mock import MagicMock, patch
from agents.base_agent import BaseAgent


def test_load_prompt(tmp_path):
    prompt_file = tmp_path / "test_prompt.md"
    prompt_file.write_text("You are a helpful analyst. Analyze: {{content}}")
    agent = BaseAgent(prompts_dir=str(tmp_path))
    prompt = agent.load_prompt("test_prompt")
    assert "You are a helpful analyst" in prompt


def test_call_claude_returns_parsed_json():
    agent = BaseAgent(prompts_dir="prompts")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='{"result": "ok"}')]
    )
    agent.client = mock_client
    result = agent.call_claude(system="You are an analyst", user_message="Analyze this")
    assert result == {"result": "ok"}


def test_call_claude_handles_markdown_json_block():
    agent = BaseAgent(prompts_dir="prompts")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='```json\n{"result": "ok"}\n```')]
    )
    agent.client = mock_client
    result = agent.call_claude(system="You are an analyst", user_message="Analyze this")
    assert result == {"result": "ok"}
