#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble the single-file edition of the guide from docs/manifest.json.

The manifest is the single source of truth for metadata and chapter order.
Per-chapter navigation blocks are stripped so the merged file has no dead links.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MANIFEST = json.loads((DOCS / "manifest.json").read_text(encoding="utf-8"))
OUT = ROOT / "深圳备婚指南.md"

NAV_BLOCK = re.compile(r"<!-- nav:start -->.*?<!-- nav:end -->\n?", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
STEP_TITLE = re.compile(r"^第 (?P<num>\d+) 步｜(?P<name>.+?)（(?P<window>T[^）]*)）$")
INTRO_TITLE = re.compile(r"^00｜(?P<name>.+)$")
APPENDIX_TITLE = re.compile(r"^附录 (?P<letter>[A-E])｜(?P<name>.+)$")


def read_chapter(rel: str) -> str:
    """Read one chapter, dropping the source-only reading navigation."""
    text = (ROOT / rel).read_text(encoding="utf-8").replace("\ufeff", "").strip()
    text = NAV_BLOCK.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text, count=1).strip()


def chapter_title(text: str) -> str:
    match = H1.search(text)
    if not match:
        raise SystemExit(f"Missing h1 heading in chapter:\n{text[:120]}")
    return match.group(1).strip()


def anchor_for(rel: str) -> str:
    name = Path(rel).name
    if name.startswith("00-"):
        return "ch00"
    match = re.match(r"(\d{2})-", name)
    if match:
        return f"ch{int(match.group(1)):02d}"
    match = re.match(r"([A-E])-", name)
    if match:
        return f"appendix-{match.group(1).lower()}"
    raise SystemExit(f"Cannot derive an anchor from {rel}")


def split_title(title: str) -> tuple[str, str, str]:
    """Return (short label, display name, time window) for the table of contents."""
    match = STEP_TITLE.match(title)
    if match:
        return f"第 {match['num']} 步", match["name"], match["window"]

    match = INTRO_TITLE.match(title)
    if match:
        return "00", match["name"], "先读"

    match = APPENDIX_TITLE.match(title)
    if match:
        name = match["name"].removesuffix("：随时查")
        return f"附录 {match['letter']}", name, "随时查"

    return title, title, ""


def build_toc(chapters: list[tuple[str, str]]) -> str:
    main_rows: list[str] = []
    appendix_rows: list[str] = []

    for rel, title in chapters:
        label, name, window = split_title(title)
        link = f"[{name}](#{anchor_for(rel)})"
        if label.startswith("附录"):
            appendix_rows.append(f"| {label} | {link} |")
        else:
            main_rows.append(f"| {label} | {link} | {window} |")

    lines = [
        "按时间读主线；附录只用来查，不用从头读。",
        "",
        "### 主线：按时间读",
        "",
        "| 阶段 | 章节 | 时间窗口 |",
        "|---|---|---|",
        *main_rows,
        "",
        "### 附录：随时查",
        "",
        "| 附录 | 内容 |",
        "|---|---|",
        *appendix_rows,
    ]
    return "\n".join(lines)


def build_header(toc: str) -> str:
    meta = MANIFEST
    return f"""---
title: {meta['title']}
subtitle: {meta['subtitle']}
version: {meta['edition']}
last_updated: {meta['last_updated']}
data_cutoff: {meta['data_cutoff']}
audience: {meta['audience']}
status: {meta['confidentiality']}
---

# {meta['title']}

> {meta['subtitle']}  
> **{meta['edition']}** ｜ 资料截止：{meta['data_cutoff']}  
> 适用：{meta['audience']} ｜ {meta['confidentiality']}  
> 价格口径：人民币；{meta['price_basis']}

---

## 全书目录

{toc}

## 五条结论

1. **先定规模档 S 和品质档 T，再看酒店。** 规模决定桌数，品质决定每桌和人员标准。
2. **桌数是最大的成本杠杆。** T2 每加 1 桌约 1.1 万；减 5 桌约省 5.5 万。
3. **只比桌价一定选错。** 把服务费、酒水、设备、备用桌算进去，才是“全包桌价”。
4. **留 10% 备用金，尾款留到交付后。** 婚礼超支几乎都发生在最后一公里。
5. **当天只有一个总指挥。** 决策权分散，是现场混乱的第一原因。

## 事实分级

| 标记 | 含义 | 怎么用 |
|---|---|---|
| **A** | 官方文件 / 政府网站 | 可直接作为办理依据 |
| **B** | 政府服务指南 / 本地办事信息 | 操作指引，办理前再确认 |
| **C** | 商业平台 / 市场公开报价 | 价格锚点，以书面报价为准 |
| **D** | 媒体案例 | 风险提示，不作为普遍事实 |

## 使用说明

本文是“决策 + 执行”手册，不是标准答案。每个家庭应按自己的宾客结构、预算、礼俗和风险偏好调整。

政策、地址、电话、价格均可能变化。办理 / 签约前，请以官方最新公布和书面报价为准。本文不构成法律、税务、投资或医疗建议。
"""


def build_footer() -> str:
    meta = MANIFEST
    return (
        f"\n---\n\n*{meta['edition']} ｜ 最后更新：{meta['last_updated']} "
        f"｜ 资料截止：{meta['data_cutoff']} ｜ {meta['confidentiality']}*\n"
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    chapters = [(rel, chapter_title(read_chapter(rel))) for rel in MANIFEST["files"]]

    parts = [build_header(build_toc(chapters))]
    for rel, _ in chapters:
        body = read_chapter(rel)
        parts.append(f'\n---\n\n<a id="{anchor_for(rel)}"></a>\n\n{body}\n')
    parts.append(build_footer())

    OUT.write_text("".join(parts), encoding="utf-8", newline="\n")
    print(
        f"Wrote {OUT.name} "
        f"({OUT.stat().st_size / 1024:.0f} KB, {len(chapters)} chapters)"
    )


if __name__ == "__main__":
    main()
