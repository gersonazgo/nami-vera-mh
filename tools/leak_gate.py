#!/usr/bin/env python3
"""Leak checker for the published results repository.

This file is vendored into the public repository as `tools/leak_gate.py` and runs
there on every push. That is deliberate: the redaction rules should be auditable
by whoever reads the results, not taken on trust. It is written in English and
depends only on the standard library so it runs anywhere with a Python.

## What it protects

The published repository contains every transcript and every judge verdict. It
must not contain the chatbot's own clinical prompt, nor the rationale the chatbot
returns alongside each reply — that rationale cites the prompt by section number,
and two hundred of them would reconstruct the protocol's structure.

The judge's reasoning is different and must stay: it comes from a separate model,
evaluates against a public rubric, and is the most useful content in the
repository. So "no reasoning anywhere" is the wrong rule; the rule is about
*where* the reasoning sits.

## Layers

1. **Structural, path-aware.** Walks every JSON and flags any `reasoning` key
   whose path is not `$.conversations[*].verdicts[*].reasoning` or
   `$.conversations[*].judge_trace[*].reasoning`.

2. **Textual.** Scans every emitted byte — JSON, Markdown, CSV — for local file
   paths, section citations, the chatbot's internal tool names, and secrets. The
   section-citation patterns are Portuguese because the rationale being excluded
   is written in Portuguese; that is the language of the thing we are keeping out,
   not of this repository.

3. **Prompt shingles.** Extracts every 8-word sequence from the clinical prompts
   and searches for each in the emitted bytes. This backs the verifiable claim
   *no 8-word passage of the protocol appears in the published bytes* without
   depending on a hand-curated list of phrases that would age with every edit.
   This layer runs only where the prompts exist — publishing even their hashes
   would be partial leakage — so the vendored copy runs the first two.

A checker that has never been seen failing is a claim, not a guarantee: the test
suite builds a deliberately poisoned tree and asserts that this one rejects it.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Finding:
    """One flagged item.

    `where` and `excerpt` exist so a human can judge in five seconds whether it is
    a leak or a false positive — the checker is deliberately noisy rather than
    clever.
    """

    file: str
    rule: str
    where: str
    excerpt: str

    def render(self) -> str:
        return f"  {self.file}\n    [{self.rule}] {self.where}\n    …{self.excerpt}…"


# The excluded rationale cites sections in at least three shapes — "Conforme 1.4",
# "Vou seguir 2.2.2", "(2.4.4.8)" — so one rule does not catch them all.
PATTERN_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("local-path", re.compile(r"/Users/|/home/[a-z]|C:\\\\Users", re.IGNORECASE)),
    (
        "section-citation",
        re.compile(
            r"\b(conforme|segundo|seç[ãa]o|secao|regra|item|nos termos d[oa])\s+\d+(\.\d+)*",
            re.IGNORECASE,
        ),
    ),
    # Three components or more, so version strings like "v1.2" and dollar amounts
    # do not collide with it.
    ("section-numeral", re.compile(r"\b\d+\.\d+\.\d+(\.\d+)*\b")),
    # Verified against the corpus: the chatbot's internal tool names appear only
    # inside the excluded rationale. They are canaries — if one leaks, the rest
    # came with it.
    (
        "tool-canary",
        re.compile(r"respond_to_patient|call_emergency_contact|notify_professional"),
    ),
    ("secret", re.compile(r"sk-ant-|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{10,}|-----BEGIN")),
)

TEXT_SUFFIXES = {".json", ".md", ".csv", ".txt", ".yml", ".yaml", ".html", ".js", ".ts", ".tsx"}

# The two paths where `reasoning` belongs to the judge and is meant to be public.
_JUDGE_REASONING = re.compile(r"\.(verdicts|judge_trace)\[\d+\]\.reasoning$")


def _excerpt(text: str, start: int, end: int, width: int = 60) -> str:
    left = max(0, start - width)
    right = min(len(text), end + width)
    return text[left:right].replace("\n", " ⏎ ")


def gate_patterns(text: str, source: str) -> list[Finding]:
    """Layer 2: textual patterns over the raw bytes of a file."""
    findings: list[Finding] = []
    for rule, pattern in PATTERN_RULES:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(source, rule, f"line {line}", _excerpt(text, match.start(), match.end()))
            )
    return findings


def _walk_reasoning(node: Any, path: str, findings: list[Finding], source: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}"
            if key == "reasoning" and not _JUDGE_REASONING.search(child):
                findings.append(Finding(source, "misplaced-reasoning", child, str(value)[:120]))
            _walk_reasoning(value, child, findings, source)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk_reasoning(item, f"{path}[{i}]", findings, source)


def gate_structure(payload: Any, source: str) -> list[Finding]:
    """Layer 1: `reasoning` outside the two paths where it belongs to the judge."""
    findings: list[Finding] = []
    _walk_reasoning(payload, "$", findings, source)
    return findings


def _normalise(text: str) -> list[str]:
    """Lowercase words, accents and punctuation removed.

    Without this, a prompt sentence reproduced with curly quotes or different
    spacing would slip past the n-gram comparison.
    """
    stripped = unicodedata.normalize("NFKD", text.lower())
    stripped = "".join(c for c in stripped if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9]+", stripped)


def prompt_shingles(prompt_files: Iterable[Path], n: int = 8) -> frozenset[int]:
    """Hashes of every n-word sequence in the clinical prompts."""
    shingles: set[int] = set()
    for path in prompt_files:
        words = _normalise(path.read_text(encoding="utf-8"))
        for i in range(len(words) - n + 1):
            shingles.add(hash(" ".join(words[i : i + n])))
    return frozenset(shingles)


def gate_shingles(
    text: str, shingles: frozenset[int], source: str, n: int = 8
) -> list[Finding]:
    """Layer 3: any n-word sequence shared with a clinical prompt."""
    if not shingles:
        return []
    words = _normalise(text)
    for i in range(len(words) - n + 1):
        window = words[i : i + n]
        if hash(" ".join(window)) in shingles:
            return [Finding(source, "prompt-passage", f"word {i}", " ".join(window))]
    return []


def run_gate(root: Path, prompts: Iterable[Path] = ()) -> list[Finding]:
    """Scan the whole tree. Returns findings; an empty list is approval."""
    shingles = prompt_shingles(prompts) if prompts else frozenset()
    findings: list[Finding] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if ".git/" in str(path):
            continue
        relative = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if path.suffix.lower() == ".json":
            try:
                findings += gate_structure(json.loads(text), relative)
            except json.JSONDecodeError:
                pass
        findings += gate_patterns(text, relative)
        findings += gate_shingles(text, shingles, relative)

    return findings


def report(findings: list[Finding], layers: str, out) -> None:
    print(f"✗ leak gate: {len(findings)} finding(s) — {layers}\n", file=out)
    for finding in findings[:40]:
        print(finding.render(), file=out)
    if len(findings) > 40:
        print(f"  … and {len(findings) - 40} more", file=out)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="repository checkout to scan")
    args = parser.parse_args(argv)

    if not args.out.is_dir():
        print(f"--out: no such directory: {args.out}", file=sys.stderr)
        return 2

    findings = run_gate(args.out)
    layers = "2 layers (clinical prompts not present here, by design)"
    if findings:
        report(findings, layers, sys.stderr)
        return 1
    print(f"✓ leak gate: no findings — {layers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
