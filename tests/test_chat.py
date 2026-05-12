from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.chat import (
    ChatTurn,
    assistant_reply_from_generation,
    build_chat_prompt,
    prepare_chat_prompt,
    stop_at_markers,
    turns_to_dicts,
)
from minigpt.tokenizer import CharTokenizer


class ChatTests(unittest.TestCase):
    def test_build_chat_prompt_adds_role_labels_and_assistant_cue(self) -> None:
        prompt = build_chat_prompt(
            [ChatTurn("user", "解释 token")],
            system_prompt="保持简洁",
        )

        self.assertIn("系统：保持简洁", prompt)
        self.assertIn("用户：解释 token", prompt)
        self.assertTrue(prompt.endswith("助手："))

    def test_chat_turn_rejects_unknown_role(self) -> None:
        with self.assertRaises(ValueError):
            ChatTurn("tool", "hello")

    def test_stop_at_markers_uses_earliest_marker(self) -> None:
        text = "这是回答\n用户：下一轮\n系统：新规则"

        self.assertEqual(stop_at_markers(text), "这是回答")

    def test_assistant_reply_from_generation_removes_context(self) -> None:
        reply = assistant_reply_from_generation("上下文助手：回答\n用户：继续", "上下文助手：")

        self.assertEqual(reply, "回答")

    def test_prepare_chat_prompt_trims_to_block_size(self) -> None:
        tokenizer = CharTokenizer.train("abcdef")

        prepared = prepare_chat_prompt(tokenizer, "abcdef", block_size=3)

        self.assertTrue(prepared.trimmed)
        self.assertEqual(prepared.original_token_count, 6)
        self.assertEqual(len(prepared.token_ids), 3)
        self.assertEqual(prepared.decoded_context, "def")

    def test_turns_to_dicts(self) -> None:
        turns = [ChatTurn("USER", "你好")]

        self.assertEqual(turns_to_dicts(turns), [{"role": "user", "content": "你好"}])


if __name__ == "__main__":
    unittest.main()
