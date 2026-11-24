#!/usr/bin/env python3
"""从 timeline.json 导出分镜稿（Markdown），方便对稿和存档

  .venv/bin/python engine/storyboard.py out/lidong
"""
import json
import sys
from pathlib import Path

TEMPLATE_CN = {
    "cover": "封面", "seasons": "四季并列", "statement": "大字陈述",
    "bigchar": "单字释义", "quote": "竖排引文", "compare": "左右对比",
    "timeline": "时间轴", "ritual": "流程三步", "food": "卡片三连",
    "outro": "结尾",
}


def fmt(s):
    m, sec = divmod(round(float(s), 1), 60)
    return f"{int(m):02d}:{sec:04.1f}"


def big_text(pr):
    for key in ("title", "char"):
        if pr.get(key):
            return pr[key]
    if pr.get("lines"):
        return " / ".join(pr["lines"])
    if pr.get("points"):
        return " / ".join(pr["points"])
    if pr.get("left") and pr.get("right"):
        return f"{pr['left'].get('title', '')} ↔ {pr['right'].get('title', '')}"
    if pr.get("items"):
        return " / ".join(x.get("t") or x.get("n") or "" for x in pr["items"])
    return ""


def main(d):
    p = Path(d) / "timeline.json"
    tl = json.loads(p.read_text(encoding="utf-8"))
    lines = [f"# 分镜稿 · {tl['meta']['title']}", "",
             f"总长 {tl['total']:.1f}s ｜ {tl['meta']['fps']}fps ｜ "
             f"{tl['meta']['width']}×{tl['meta']['height']} ｜ "
             f"配音 {tl['meta'].get('voice_name', 'edge-tts')}", "",
             "| # | 时间 | 模板 | 屏幕大字 | 旁白 |",
             "|---|---|---|---|---|"]
    for s in tl["scenes"]:
        pr = s["props"]
        big = str(big_text(pr)).replace("|", "｜").replace("\n", " ")
        narr = (s.get("narration") or "").replace("|", "｜")
        lines.append(f"| {s['index'] + 1} | {fmt(s['start'])}–{fmt(s['start'] + s['dur'])} | "
                     f"{TEMPLATE_CN.get(s['template'], s['template'])} | {big} | {narr} |")
    out = p.parent / "storyboard.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
