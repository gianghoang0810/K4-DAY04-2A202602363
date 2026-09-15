import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from chat import run_model_tool_loop
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools


class IntegrationTests(unittest.TestCase):
    def test_schema_and_registry(self):
        declarations = load_tool_declarations(Path(__file__).resolve().parents[1] / "artifacts/tools.yaml")
        self.assertEqual({d["name"] for d in declarations}, set(TOOL_FUNCTIONS))
        self.assertEqual(len([d for d in declarations if d["name"] == "detect_duplicate_ticket"]), 1)
        self.assertEqual(len(to_openai_tools(declarations)), 10)

    def test_chat_dispatches_bonus_and_returns_result_to_provider(self):
        calls = []
        class FakeProvider:
            def complete(self, messages, tools, **kwargs):
                calls.append(messages.copy())
                if len(calls) == 1:
                    return SimpleNamespace(text=None, tool_calls=[ToolCall(
                        name="detect_duplicate_ticket", args={"summary": "VPN timeout", "asset_id": "LT-204"}
                    )])
                return SimpleNamespace(text=json.dumps({"intent": "duplicate_review", "action": "reply",
                    "reply": "Review existing ticket LAB-1234ABCD.", "evidence_ids": ["LAB-1234ABCD"]}), tool_calls=[])
        candidate = {"tool": "detect_duplicate_ticket", "status": "candidates_found",
                     "matches": [{"ticket_id": "LAB-1234ABCD", "similarity": 1}]}
        with patch.dict(TOOL_FUNCTIONS, {"detect_duplicate_ticket": lambda **kwargs: candidate}):
            result = run_model_tool_loop(provider=FakeProvider(), messages=[{"role": "user", "content": "Check duplicates"}],
                                         tools=[], model=None, max_tool_rounds=3)
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["tool_events"][0]["result"], candidate)
        self.assertIn("LAB-1234ABCD", calls[1][-1]["content"])
        self.assertEqual(len(result["tool_events"]), 1)


if __name__ == "__main__":
    unittest.main()
