"""modelcard —— 自检测试。

生成模型说明卡模板，把来源、适用范围与已知限制写成必须填的字段。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import modelcard  # noqa: E402


class TestModelCard(unittest.TestCase):
    def test_vague_claim_is_flagged(self):
        text = ("# 模型标识\n- 名称：x\n\n# 已知限制\n"
                "- 已知失效条件：表现良好\n")
        a = modelcard.audit_card(text)
        self.assertGreaterEqual(a["summary"]["vague"], 1)

    def test_unknown_is_accepted_not_flagged(self):
        text = ("# 模型标识\n- 名称：x\n\n# 已知限制\n"
                "- 已知失效条件：不知道\n")
        a = modelcard.audit_card(text)
        self.assertEqual(a["summary"]["vague"], 0)

    def test_placeholder_is_flagged(self):
        text = ("# 模型标识\n- 名称：x\n\n# 已知限制\n"
                "- 已知失效条件：TODO\n")
        a = modelcard.audit_card(text)
        self.assertGreaterEqual(a["summary"]["placeholders"], 1)

    def test_source_is_required(self):
        text = ("# 模型标识\n- 名称：x\n\n# 已知限制\n"
                "- 已知失效条件：在低温下会误判\n")
        a = modelcard.audit_card(text)
        self.assertGreaterEqual(a["summary"]["no_source"], 1)

    def test_source_marker_satisfies_requirement(self):
        text = ("# 模型标识\n- 名称：x\n\n# 已知限制\n"
                "- 已知失效条件：在低温下会误判 来源：https://example.com/a\n")
        a = modelcard.audit_card(text)
        self.assertEqual(a["summary"]["no_source"], 0)

    def test_template_has_all_fields(self):
        tpl = modelcard.build_template("gpt-4o", "客服问答")
        for sec, fields in modelcard.SECTIONS:
            for f in fields:
                self.assertIn(f, tpl)
