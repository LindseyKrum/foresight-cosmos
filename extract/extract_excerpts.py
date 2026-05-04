#!/usr/bin/env python3
"""
Foresight Cosmos — Excerpt extractor.

For each signal in cosmos.json that lacks an `excerpt` field, finds the
source report's raw text and asks Claude to quote the 1-2 sentences that
most directly support the signal.

Uses raw_extracts.json (4 000-char text per report) as the text source.
Falls back to re-reading the PDF via PyMuPDF if the report isn't in the
raw extracts file.

Usage:
  python extract_excerpts.py [--limit N] [--force]

  --limit N    Process only N signals (useful for testing)
  --force      Re-extract even if signal already has an excerpt
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import anthropic

COSMOS_PATH   = Path("../data/cosmos.json")
EXTRACTS_PATH = Path("../data/raw_extracts.json")
PDFS_DIR      = Path("../pdfs")

EXCERPT_PROMPT = """\
You are finding a direct quote from a foresight report.

Signal name: {name}
Signal description: {description}

Report text:
{text}

Find the 1-2 consecutive sentences from the report text that most directly
support or evidence this signal. Return only those exact sentences, verbatim
from the text above — no paraphrasing, no additions, no commentary.

If you cannot find relevant text, return the single word: NONE
"""


def build_text_index(extracts: list) -> dict:
    """Build a dict from report stem → text."""
    index = {}
    for item in extracts:
        stem = Path(item["filename"]).stem
        text = item.get("text") or ""
        if text.strip():
            index[stem] = text
    return index


def try_read_pdf(pdf_path: Path, max_chars: int = 12_000) -> str:
    """Read full PDF text as a fallback."""
    try:
        import fitz
        doc  = fitz.open(str(pdf_path))
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text[:max_chars]
    except Exception as e:
        print(f"    ⚠ PDF read failed: {e}")
        return ""


def extract_excerpt(client: anthropic.Anthropic, signal: dict, text: str) -> str | None:
    prompt = EXCERPT_PROMPT.format(
        name=signal["name"],
        description=signal["description"],
        text=text,
    )
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        result = msg.content[0].text.strip()
        if result.upper() == "NONE" or len(result) < 15:
            return None
        return result
    except Exception as e:
        print(f"    ⚠ API error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Add excerpt quotes to signals")
    parser.add_argument("--limit",  type=int, default=None, help="Max signals to process")
    parser.add_argument("--force",  action="store_true",    help="Re-extract existing excerpts")
    parser.add_argument("--api-key", default=None)
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY env var or pass --api-key.")
        sys.exit(1)

    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)
    with open(EXTRACTS_PATH) as f:
        extracts = json.load(f)

    text_index = build_text_index(extracts)
    print(f"Loaded {len(text_index)} report texts from raw_extracts.json")

    client = anthropic.Anthropic(api_key=api_key)
    signals = cosmos["signals"]

    # Determine which signals need excerpts
    targets = [
        s for s in signals
        if args.force or not s.get("excerpt")
    ]
    if args.limit:
        targets = targets[:args.limit]

    print(f"Processing {len(targets)} signals (of {len(signals)} total)...")

    filled = 0
    skipped = 0

    for i, sig in enumerate(targets):
        print(f"  [{i+1}/{len(targets)}] {sig['id']} — {sig['name'][:50]}")

        # Pick first source with matching text
        text = ""
        for src in sig.get("sources", []):
            report_stem = src.get("report", "")
            if report_stem in text_index:
                text = text_index[report_stem]
                break

        # Fallback: try reading PDF
        if not text:
            for src in sig.get("sources", []):
                report_stem = src.get("report", "")
                pdf_candidates = list(PDFS_DIR.glob(f"{report_stem}.*"))
                if pdf_candidates:
                    print(f"    → fallback: reading PDF {pdf_candidates[0].name}")
                    text = try_read_pdf(pdf_candidates[0])
                    if text:
                        # Cache it for later signals
                        text_index[report_stem] = text
                    break

        if not text:
            print(f"    ✗ no text available, skipping")
            skipped += 1
            continue

        excerpt = extract_excerpt(client, sig, text)

        if excerpt:
            # Find the actual signal object in cosmos and update it
            for s in cosmos["signals"]:
                if s["id"] == sig["id"]:
                    s["excerpt"] = excerpt
                    break
            filled += 1
            print(f"    ✓ {excerpt[:80]}...")
        else:
            print(f"    ✗ no relevant quote found")
            skipped += 1

        # Throttle to avoid rate limits
        if (i + 1) % 10 == 0:
            time.sleep(1)

    # Save
    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print(f"\n✓ Done. {filled} excerpts added, {skipped} skipped.")
    print(f"  cosmos.json updated at {COSMOS_PATH}")


if __name__ == "__main__":
    main()
