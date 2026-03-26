#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional


def _join_source(src) -> str:
    if isinstance(src, list):
        return "".join(src)
    return str(src or "")


def detect_language(src) -> Optional[str]:
    text_raw = _join_source(src)
    lines = [line for line in text_raw.splitlines() if line.strip()]
    if not lines:
        return None

    first = lines[0].lstrip()
    if first.startswith("%%"):
        tag = first[2:].split()[0].lower() if first[2:].split() else ""
        if tag in ("cpp", "c++"):
            return "cpp"
        if tag == "c":
            return "c"
        if tag in ("python", "py"):
            return "python"

    text = "\n".join(lines)
    lower = text.lower()

    score = {"python": 0, "cpp": 0, "c": 0}

    py_tokens = [
        "import ",
        "from ",
        "def ",
        "print(",
        "lambda ",
        "none",
        "true",
        "false",
        "try:",
        "except",
        "with ",
        "yield ",
        "async ",
        "await ",
        "elif ",
        "self",
    ]
    cpp_tokens = [
        "#include",
        "std::",
        "using namespace std",
        "cout",
        "cin",
        "vector<",
        "string",
        "new ",
        "delete",
        "template<",
        "namespace ",
        "nullptr",
        "auto ",
        "::",
    ]
    c_tokens = [
        "#include",
        "printf(",
        "scanf(",
        "malloc(",
        "free(",
        "sizeof",
        "int main",
        "char *",
        "struct ",
        "typedef ",
        "enum ",
        "fopen(",
        "fgets(",
        "puts(",
        "gets(",
    ]

    for tok in py_tokens:
        if tok in lower or tok in text:
            score["python"] += 2
    for tok in cpp_tokens:
        if tok in lower or tok in text:
            score["cpp"] += 2
    for tok in c_tokens:
        if tok in lower or tok in text:
            score["c"] += 2

    if "iostream" in lower or "std::" in text or "using namespace std" in lower:
        score["cpp"] += 3
    if "stdio.h" in lower or "stdlib.h" in lower:
        score["c"] += 3

    if score["python"] > score["cpp"] and score["python"] > score["c"]:
        return "python"
    if score["cpp"] > score["c"]:
        return "cpp"
    if score["c"] > 0:
        return "c"

    # Python fallback by indentation/colon style
    if re.search(r"^\s*(def|class|for|while|if|elif|else|try|with)\b.*:\s*$", text, re.M):
        return "python"

    return None


def update_cell_metadata(cell: dict, lang: Optional[str]) -> bool:
    md = cell.setdefault("metadata", {})
    changed = False

    if lang is None:
        if "language" in md:
            md.pop("language", None)
            changed = True
        vs = md.get("vscode")
        if isinstance(vs, dict) and "languageId" in vs:
            vs.pop("languageId", None)
            changed = True
            if not vs:
                md.pop("vscode", None)
        return changed

    display, language_id = {
        "cpp": ("C++", "cpp"),
        "c": ("C", "c"),
        "python": ("python", "python"),
    }[lang]

    if md.get("language") != display:
        md["language"] = display
        changed = True

    vs = md.get("vscode")
    if not isinstance(vs, dict):
        vs = {}
        md["vscode"] = vs
        changed = True

    if vs.get("languageId") != language_id:
        vs["languageId"] = language_id
        changed = True

    return changed


def process_notebook(path: Path) -> tuple[bool, int]:
    nb = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    code_cells = 0

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        code_cells += 1
        lang = detect_language(cell.get("source", ""))
        if update_cell_metadata(cell, lang):
            changed = True

    if changed:
        path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")

    return changed, code_cells


def main() -> int:
    raw_target = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parent)
    raw_target = raw_target.strip().strip('"')
    while raw_target.endswith('"'):
        raw_target = raw_target[:-1]
    target = Path(raw_target)
    target = target.resolve()

    if not target.exists():
        print(f"Target does not exist: {target}")
        return 1

    notebooks = sorted(target.rglob("*.ipynb"))
    updated = 0
    scanned = 0
    code_cells = 0

    for nb_path in notebooks:
        scanned += 1
        try:
            ch, cells = process_notebook(nb_path)
            code_cells += cells
            if ch:
                updated += 1
                print(f"UPDATED: {nb_path}")
        except Exception as exc:
            print(f"SKIP (error): {nb_path} -> {exc}")

    print(f"DONE. scanned={scanned}, updated={updated}, code_cells={code_cells}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
