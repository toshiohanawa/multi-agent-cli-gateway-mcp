import unittest

from mcp.bridge import (
    MAX_HISTORY_TURNS,
    Decision,
    DebateSession,
    Turn,
    _trim_history,
    build_next_prompt,
)


class BuildNextPromptTests(unittest.TestCase):
    def test_build_next_prompt_includes_last_response_and_recent_context(self):
        decision = Decision(type="adopt_codex")
        turns = [
            Turn(user_instruction="u0", codex_output="old0", responder="codex"),
            Turn(user_instruction="u1", claude_output="old1", responder="claude"),
            Turn(user_instruction="u2", codex_output="old2", responder="codex"),
            Turn(user_instruction="u3", claude_output="last_claude", responder="claude"),
        ]
        last_turn = turns[-1]
        prompt = build_next_prompt(
            decision,
            last_turn,
            next_responder="codex",
            conversation_history=turns,
            mode="critique",
        )

        self.assertIn("Proceed using Codex's approach", prompt)
        self.assertIn("Claude said: last_claude", prompt)
        self.assertIn("Claude: old1", prompt)
        self.assertIn("Codex: old2", prompt)
        self.assertIn("Claude: last_claude", prompt)
        # The oldest turn should be trimmed out of context (only last 3 kept)
        self.assertNotIn("old0", prompt)
        self.assertIn("You are the proposer", prompt)


class HistoryTrimTests(unittest.TestCase):
    def test_trim_history_keeps_configured_limit(self):
        session = DebateSession(active=True)
        for idx in range(MAX_HISTORY_TURNS + 10):
            session.history.append(Turn(user_instruction=f"u{idx}", codex_output=f"c{idx}", responder="codex"))

        _trim_history(session)
        self.assertEqual(len(session.history), MAX_HISTORY_TURNS)
        # Oldest entries should have been discarded
        self.assertEqual(session.history[0].codex_output, f"c{10}")


if __name__ == "__main__":
    unittest.main()
