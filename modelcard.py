"""modelcard —— 给模型写一张说得清来源的说明卡。

设计原则：
1. **「不知道」是合法答案**。宁可让卡片半空，也不填满无法核对的漂亮话。
2. **来源是必填字段**。每个结论要么给来源，要么明确写「不知道」。
3. **指标要写版本**。同名指标在不同评测里未必指同一件事。

仅依赖 Python 标准库。

用法:
    python modelcard.py --help
    python modelcard.py --model gpt-4o --use-case "客户问答" --out card.md
    python modelcard.py --init --out card.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# ---------------------------------------------------------------------------
# 卡片结构
# ---------------------------------------------------------------------------

SECTIONS = [
    ("模型标识", ["名称", "版本", "提供方", "发布日期", "上下文长度"]),
    ("适用范围", ["适用场景", "不适用的场景"]),
    ("来源标注", ["每个结论的来源", "指标定义与版本"]),
    ("已知限制", ["已知失效条件", "已知的偏差方向"]),
    ("评测记录", ["评测数据集", "评测时间", "评测结果"]),
]

# 各类字段的来源要求：哪些字段必须有来源，哪些允许写「不知道」
SOURCE_REQUIRED = {
    "已知失效条件": True,
    "已知的偏差方向": True,
    "评测结果": True,
    "指标定义与版本": True,
    "每个结论的来源": True,
}

# 结论类字段：写具体内容才算合格，不能是套话
VAGUE_PATTERNS = (
    "表现良好", "效果不错", "质量较高", "性能优秀", "业内领先",
    "大幅提升", "显著改善", "广泛验证", "经过充分测试",
)

PLACEHOLDER_TOKENS = ("TBD", "TODO", "待补充", "暂缺", "xxx", "???")

UNKNOWN = "不知道"


# ---------------------------------------------------------------------------
# 检查
# ---------------------------------------------------------------------------

def is_vague(text: str) -> bool:
    """判断是不是无法核对的套话。"""
    low = text.lower()
    return any(p in low for p in VAGUE_PATTERNS)


def has_placeholder(text: str) -> bool:
    """判断有没有占位符残留。"""
    low = text.strip().lower()
    return any(t.lower() in low for t in PLACEHOLDER_TOKENS)


def audit_card(text: str) -> dict:
    """审查一张说明卡。"""
    sections = parse_sections(text)

    filled: list[dict] = []
    missing: list[dict] = []
    vague: list[dict] = []
    placeholders: list[dict] = []
    no_source: list[dict] = []

    for sec_name, fields in SECTIONS:
        for field in fields:
            value = sections.get(f"{sec_name}·{field}", "")
            item = {"section": sec_name, "field": field, "value": value}

            if not value or value.strip() == UNKNOWN:
                missing.append(item)
                continue

            filled.append(item)

            if has_placeholder(value):
                placeholders.append(item)
            if is_vague(value):
                vague.append(item)
            if SOURCE_REQUIRED.get(field) and not has_source_marker(value):
                no_source.append(item)

    return {
        "filled": filled,
        "missing": missing,
        "vague": vague,
        "placeholders": placeholders,
        "no_source": no_source,
        "total_fields": sum(len(f) for _, f in SECTIONS),
        "summary": {
            "filled": len(filled),
            "missing": len(missing),
            "vague": len(vague),
            "placeholders": len(placeholders),
            "no_source": len(no_source),
        },
    }


def has_source_marker(value: str) -> bool:
    """值里是否带了来源标记（http 链接 / 引用编号 / 文件名）。"""
    import re
    if re.search(r"https?://", value):
        return True
    if re.search(r"\[[\w\-]+\]", value):      # [ref1]
        return True
    if re.search(r"(来源|引用|出自|见)\s*[:：]", value):
        return True
    return False


def parse_sections(text: str) -> dict[str, str]:
    """解析卡片文本成 {「章节·字段」: 值}。"""
    out: dict[str, str] = {}
    current_section = ""
    current_field = ""
    buf: list[str] = []

    def flush() -> None:
        if current_section and current_field:
            out[f"{current_section}·{current_field}"] = "\n".join(buf).strip()

    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            flush()
            current_section = m.group(1).strip()
            current_field = ""
            buf = []
            continue
        m = re.match(r"^\s*[-*]\s+\*?\*?([^*:：]+)\*?\*?\s*[:：]\s*(.*)$", line)
        if m:
            flush()
            current_field = m.group(1).strip()
            buf = [m.group(2).strip()]
            continue
        if current_field:
            buf.append(line.strip())
    flush()
    return out


# ---------------------------------------------------------------------------
# 生成模板
# ---------------------------------------------------------------------------

def build_template(model: str, use_case: str) -> str:
    """生成一张空卡片模板。字段值默认写「不知道」。"""
    lines: list[str] = []
    lines.append(f"# {model} 模型说明卡")
    lines.append("")
    lines.append("> 填写规则：每个结论要么给出来源，要么明确写「不知道」。")
    lines.append("> 写「不知道」比写无法核对的话有用。")
    lines.append("")
    for sec_name, fields in SECTIONS:
        lines.append(f"## {sec_name}")
        lines.append("")
        for field in fields:
            default = UNKNOWN
            if sec_name == "模型标识" and field == "名称":
                default = model
            if sec_name == "适用范围" and field == "适用场景" and use_case:
                default = use_case
            lines.append(f"- **{field}**：{default}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(audit: dict) -> str:
    out: list[str] = []
    s = audit["summary"]
    out.append("模型说明卡审查")
    out.append("=" * 60)
    out.append(f"字段 {audit['total_fields']} 个 ｜ 已填 {s['filled']} ｜ "
               f"空/未知 {s['missing']} ｜ 套话 {s['vague']} ｜ "
               f"占位符 {s['placeholders']} ｜ 缺来源 {s['no_source']}")
    out.append("")

    if audit["missing"]:
        out.append("空着或写「不知道」的字段：")
        for m in audit["missing"]:
            out.append(f"  · {m['section']} · {m['field']}")
        out.append("")

    if audit["vague"]:
        out.append("无法核对的套话（建议改写或写「不知道」）：")
        for v in audit["vague"]:
            out.append(f"  · {v['section']} · {v['field']}：{v['value'][:60]}")
        out.append("")

    if audit["placeholders"]:
        out.append("占位符残留：")
        for p in audit["placeholders"]:
            out.append(f"  · {p['section']} · {p['field']}")
        out.append("")

    if audit["no_source"]:
        out.append("这些字段应该有来源（链接、引用编号或「来源：」）：")
        for n in audit["no_source"]:
            out.append(f"  · {n['section']} · {n['field']}")
        out.append("")

    if not audit["missing"] and not audit["vague"] and not audit["no_source"]:
        out.append("这张卡的内容都带得住了。")
    return "\n".join(out).rstrip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="modelcard",
        description="给模型写一张说得清来源的说明卡（仅依赖标准库）",
        epilog=(
            "示例：\n"
            "  python modelcard.py --init --model gpt-4o --out card.md\n"
            "  python modelcard.py --check card.md\n"
            "  python modelcard.py --check card.md --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--init", action="store_true", help="生成一张空模板")
    ap.add_argument("--check", help="审查已有的卡片")
    ap.add_argument("--model", default="", help="模型名称")
    ap.add_argument("--use-case", default="", help="适用场景")
    ap.add_argument("--out", help="输出文件路径")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.init:
        if not args.model:
            print("--init 需要 --model。", file=sys.stderr)
            return 2
        text = build_template(args.model, args.use_case)
        if args.out:
            try:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(text)
            except OSError as e:
                print(f"写不了文件：{e}", file=sys.stderr)
                return 2
            print(f"已写入模板 {args.out}")
        else:
            print(text)
        return 0

    if not args.check:
        print("需要 --init 或 --check 其中之一。", file=sys.stderr)
        return 2

    try:
        text = open(args.check, "r", encoding="utf-8").read()
    except OSError as e:
        print(f"读不了卡片：{e}", file=sys.stderr)
        return 2

    audit = audit_card(text)

    if args.json:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return 0

    print(render(audit))
    s = audit["summary"]
    return 1 if (s["vague"] or s["placeholders"] or s["no_source"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
