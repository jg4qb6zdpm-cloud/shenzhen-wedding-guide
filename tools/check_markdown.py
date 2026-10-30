#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quality checks for the Markdown guide.

Checks:
1. Markdown tables: consistent column counts and valid separator rows.
2. Heading levels: never jump from hN to hN+2.
3. Sample budgets: the three 20-table budgets add up and appear in appendix A.
4. Stage chapters: standard section order and a valid navigation block.
5. Manifest: every chapter is listed exactly once and every file exists.
6. Relative links: every local Markdown link resolves.
7. Versions: the current version appears in all reader-facing deliverables.
8. Merged file: anchors present, no source-only navigation blocks.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MANIFEST = json.loads((DOCS / "manifest.json").read_text(encoding="utf-8"))
VERSION = MANIFEST["edition"].rsplit("·", 1)[-1].strip()

TEXT_FILES = sorted(DOCS.glob("*.md")) + [
    ROOT / "README.md",
    ROOT / "深圳备婚指南.md",
    ROOT / "深圳备婚一页纸.md",
    ROOT / "CHANGELOG.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "LICENSE",
    ROOT / "templates" / "预算与清单模板.md",
    ROOT / "templates" / "婚博会与砍价工具包.md",
    ROOT / "data" / "README.md",
    ROOT / "research" / "调研说明.md",
    ROOT / "research" / "来源清单.md",
    ROOT / "archive" / "README.md",
    ROOT / "tools" / "README.md",
]

STAGE_MARKERS = (
    "这个阶段，你只需要做 3 件事",
    "先看：时间、钱、交付物",
    "这个阶段最容易踩的",
    "本阶段检查清单",
    "进入下一步之前",
)

NAV_BLOCK = re.compile(
    r"<!-- nav:start -->\n(?P<body>.*?)\n<!-- nav:end -->", re.S
)
LINK = re.compile(r"\[[^\]]*\]\((?P<target><[^>]+>|[^)\s]+)\)")
FENCED_CODE = re.compile(r"^```.*?^```\s*$", re.M | re.S)
INLINE_CODE = re.compile(r"`[^`\n]+`")


def split_row(line: str) -> list[str]:
    """Split a pipe table row, ignoring escaped pipes."""
    body = line.strip().strip("|")
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", body)]


def check_tables(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            i += 1
            continue
        start = i
        block: list[str] = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 2:
            errors.append(f"{path.name}:{start + 1}: table has fewer than 2 rows")
            continue
        widths = {len(split_row(row)) for row in block}
        if len(widths) != 1:
            errors.append(
                f"{path.name}:{start + 1}: table column mismatch {sorted(widths)}"
            )
        sep = split_row(block[1])
        if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in sep):
            errors.append(f"{path.name}:{start + 2}: invalid separator row")
    return errors


def check_headings(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    prev = 0
    for lineno, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^(#{1,6})\s+", line)
        if not match:
            continue
        level = len(match.group(1))
        if prev and level > prev + 1:
            errors.append(
                f"{path.name}:{lineno}: heading jumps from h{prev} to h{level}"
            )
        prev = level
    return errors


def check_links(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    cleaned = INLINE_CODE.sub("", FENCED_CODE.sub("", text))
    for lineno, line in enumerate(cleaned.splitlines(), start=1):
        for match in LINK.finditer(line):
            target = match.group("target")
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            if target.startswith("#"):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            if not (path.parent / target).resolve().exists():
                errors.append(f"{path.name}:{lineno}: broken link {target!r}")
    return errors


def check_stage_structure() -> list[str]:
    """Every stage chapter follows the same reading rhythm, in the same order."""
    errors: list[str] = []
    for path in sorted(DOCS.glob("0[1-9]-*.md")):
        text = path.read_text(encoding="utf-8")
        positions: list[int] = []
        for marker in STAGE_MARKERS:
            position = text.find(marker)
            if position < 0:
                errors.append(f"{path.name}: missing stage marker {marker!r}")
            positions.append(position)
        found = [position for position in positions if position >= 0]
        if len(found) == len(positions) and found != sorted(found):
            errors.append(f"{path.name}: stage sections are out of order")

    intro = (DOCS / "00-开始之前.md").read_text(encoding="utf-8")
    for marker in ("先看：你现在在哪", "10 个词先搞懂", "五种情况，五种读法"):
        if marker not in intro:
            errors.append(f"00-开始之前.md: missing {marker!r}")
    return errors


def check_manifest() -> list[str]:
    errors: list[str] = []
    files: list[str] = MANIFEST["files"]
    if len(files) != len(set(files)):
        errors.append("manifest: duplicate chapter entries")

    for rel in files:
        if not (ROOT / rel).is_file():
            errors.append(f"manifest: missing file {rel!r}")

    listed = {Path(rel).name for rel in files}
    actual = {path.name for path in DOCS.glob("*.md")} - {"README.md"}
    for name in sorted(actual - listed):
        errors.append(f"manifest: chapter not listed {name!r}")
    for name in sorted(listed - actual):
        errors.append(f"manifest: listed chapter does not exist {name!r}")
    return errors


def expected_anchor(rel: str) -> str:
    name = Path(rel).name
    if name.startswith("00-"):
        return "ch00"
    match = re.match(r"0(\d)-", name)
    if match:
        return f"ch{int(match.group(1)):02d}"
    match = re.match(r"([A-E])-", name)
    if match:
        return f"appendix-{match.group(1).lower()}"
    return ""


def check_navigation() -> list[str]:
    errors: list[str] = []
    files: list[str] = MANIFEST["files"]
    for index, rel in enumerate(files):
        text = (ROOT / rel).read_text(encoding="utf-8")
        blocks = NAV_BLOCK.findall(text)
        if len(blocks) != 1:
            errors.append(f"{Path(rel).name}: expected exactly one nav block")
            continue
        block = blocks[0]
        if "[本书目录](README.md)" not in block:
            errors.append(f"{Path(rel).name}: nav block misses the index link")
        if index > 0 and Path(files[index - 1]).name not in block:
            errors.append(f"{Path(rel).name}: nav block misses the previous link")
        if index < len(files) - 1 and Path(files[index + 1]).name not in block:
            errors.append(f"{Path(rel).name}: nav block misses the next link")
    return errors


def check_master() -> list[str]:
    errors: list[str] = []
    master = (ROOT / "深圳备婚指南.md").read_text(encoding="utf-8")
    if "<!-- nav:" in master:
        errors.append("master: source-only nav block leaked into the merged file")
    if VERSION not in master:
        errors.append(f"master: missing current version {VERSION!r}")
    for rel in MANIFEST["files"]:
        anchor = expected_anchor(rel)
        if f'<a id="{anchor}"></a>' not in master:
            errors.append(f"master: missing anchor {anchor!r}")
    return errors


def check_budget_math() -> list[str]:
    """Verify the three 20-table sample budgets shown in appendix A."""
    errors: list[str] = []
    expected = {
        "T1": {
            "items": [12.0, 1.2, 0.6, 4.0, 2.5, 0.8, 0.8, 0.5, 1.0, 1.0],
            "subtotal": 24.4,
            "reserve": 2.44,
            "total": 26.8,
        },
        "T2": {
            "items": [16.0, 1.6, 0.8, 6.0, 3.5, 1.2, 1.5, 0.7, 1.6, 1.5],
            "subtotal": 34.4,
            "reserve": 3.44,
            "total": 37.8,
        },
        "T3": {
            "items": [20.0, 3.0, 1.2, 8.0, 4.5, 2.0, 2.5, 1.0, 3.0, 2.5],
            "subtotal": 47.7,
            "reserve": 4.77,
            "total": 52.5,
        },
    }

    appendix = DOCS / "A-价格标准.md"
    text = appendix.read_text(encoding="utf-8")
    parts = text.split("### 20 桌对照", 1)
    table = parts[1].split("###", 1)[0] if len(parts) == 2 else ""
    if not table:
        errors.append("A-价格标准.md: missing the 20-table sample budget section")

    for tier, data in expected.items():
        subtotal = round(sum(data["items"]), 2)
        reserve = round(subtotal * 0.10, 2)
        total = round(subtotal + reserve, 2)
        if subtotal != data["subtotal"]:
            errors.append(
                f"A-价格标准.md: {tier} subtotal {subtotal} != {data['subtotal']}"
            )
        if reserve != data["reserve"]:
            errors.append(
                f"A-价格标准.md: {tier} reserve {reserve} != {data['reserve']}"
            )
        if abs(total - data["total"]) > 0.05:
            errors.append(f"A-价格标准.md: {tier} total {total} != {data['total']}")
        for value in (data["subtotal"], data["reserve"], data["total"]):
            if f"{value}" not in table:
                errors.append(f"A-价格标准.md: {tier} missing value {value} in table")
    return errors


def check_versions() -> list[str]:
    errors: list[str] = []
    required = {
        "README.md": VERSION,
        "深圳备婚一页纸.md": VERSION,
        "docs/E-工具与来源.md": VERSION,
        "templates/预算与清单模板.md": VERSION,
        "templates/婚博会与砍价工具包.md": VERSION,
    }
    for rel, version in required.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        if version not in text:
            errors.append(f"{rel}: missing current version {version!r}")
    if VERSION not in MANIFEST["edition"]:
        errors.append("manifest: edition does not contain the current version")
    return errors


def main() -> int:
    all_errors: list[str] = []
    for path in TEXT_FILES:
        if not path.is_file():
            all_errors.append(f"{path.name}: missing expected file")
            continue
        text = path.read_text(encoding="utf-8")
        all_errors += check_tables(path, text)
        all_errors += check_headings(path, text)
        all_errors += check_links(path, text)

    all_errors += check_manifest()
    all_errors += check_navigation()
    all_errors += check_stage_structure()
    all_errors += check_budget_math()
    all_errors += check_versions()
    all_errors += check_master()

    if all_errors:
        print("FAILED")
        for error in all_errors:
            print(" -", error)
        return 1
    print(f"OK: {len(TEXT_FILES)} files checked, version {VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
