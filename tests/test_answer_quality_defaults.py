from __future__ import annotations

import unittest

from book_research_agent.cli import build_parser
from book_research_agent.core.answering import (
    DEFAULT_ANSWER_TOP_K,
    DEFAULT_CANON_TOP_K,
    DEFAULT_COMPARE_TOP_K,
    DEFAULT_CONTRADICT_TOP_K,
)


class AnswerQualityDefaultsTests(unittest.TestCase):
    def test_answer_facing_cli_modes_use_mode_aware_top_k_defaults(self) -> None:
        parser = build_parser()

        answer_args = parser.parse_args(["answer", "auditor"])
        canon_args = parser.parse_args(["canon", "auditor"])
        compare_args = parser.parse_args(["compare", "auditor", "old man"])
        contradict_args = parser.parse_args(
            ["contradict", "auditor as protector", "auditor as destroyer"]
        )

        self.assertEqual(answer_args.top_k, DEFAULT_ANSWER_TOP_K)
        self.assertEqual(canon_args.top_k, DEFAULT_CANON_TOP_K)
        self.assertEqual(compare_args.top_k, DEFAULT_COMPARE_TOP_K)
        self.assertEqual(contradict_args.top_k, DEFAULT_CONTRADICT_TOP_K)


if __name__ == "__main__":
    unittest.main()
