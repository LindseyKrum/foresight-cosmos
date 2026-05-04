#!/usr/bin/env python3
"""
Foresight Cosmos — Horizon tagger.

For each signal in cosmos.json, determines the expected timeframe
(near / medium / far) and extracts any specific forecast year mentioned
in the source report text.

Adds `horizon` ("near"|"medium"|"far") and optional `horizonYear` (int)
fields to each signal, then saves cosmos.json.

Horizon definitions:
  near   — materialising within ~3 years (by ~2028)
  medium — 3–8 years out (2028–2033)
  far    — 8+ years away (2034+)

Usage:
  python extract_horizons.py [--limit N] [--force]

  --limit N   Process only N signals (useful for testing)
  --force     Re-tag signals that already have a horizon field
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

PROMPT = """\
You are tagging a foresight signal with a time horizon.

Signal name: {name}
Signal description: {description}
Source report text (excerpt):
{text}

Task: decide which time horizon this signal points to, and extract any \
specific target year if one is mentioned.

Horizon definitions:
  "near"   = expected within ~3 years (by ~2028)
  "medium" = expected in 3–8 years (2028–2033)
  "far"    = expected in 8+ years (2034 or beyond)

Return ONLY valid JSON — no prose, no markdown fences:
{{"horizon": "near"|"medium"|"far", "horizonYear": <4-digit integer or null>}}

Rules:
- If no specific year is mentioned, set horizonYear to null.
- If the signal is about something already happening (current trend), use "near".
- If a year is given but is before 2025, treat the horizon as "near" with null year.
- Most signals in annual trend reports are near-term unless stated otherwise.
"""


def build_text_index(extracts: list) -> dict:
    return {Path(e["filename"]).stem: (e.get("text") or "") for e in extracts}


def tag_signal(client: anthropic.Anthropic, sig: dict, text: str) -> dict | None:
    prompt = PROMPT.format(
        name=sig["name"],
        description=sig["description"],
        text=text[:2500] if text else "(no source text available)",
    )
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=64,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r'^```(?:json)?\n?', '', raw)
        raw = re.sub(r'\n?```$', '', raw)
        result = json.loads(raw)
        horizon = result.get("horizon", "near")
        if horizon not in ("near", "medium", "far"):
            horizon = "near"
        yr = result.get("horizonYear")
        if yr is not None:
            try:
                yr = int(yr)
                if not (2025 <= yr <= 2055):
                    yr = None
            except (ValueError, TypeError):
                yr = None
        return {"horizon": horizon, "horizonYear": yr}
    except Exception as e:
        print(f"    ⚠ {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Tag signals with time horizons")
    parser.add_argument("--limit",   type=int,  default=None, help="Max signals to process")
    parser.add_argument("--force",   action="store_true",     help="Re-tag existing horizons")
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
    print(f"Loaded {len(text_index)} report texts.")

    client = anthropic.Anthropic(api_key=api_key)
    signals = cosmos["signals"]

    targets = [s for s in signals if args.force or not s.get("horizon")]
    if args.limit:
        targets = targets[:args.limit]

    print(f"Tagging {len(targets)} signals (of {len(signals)} total)...")

    near = medium = far = errors = 0

    for i, sig in enumerate(targets):
        print(f"  [{i+1}/{len(targets)}] {sig['id']}  {sig['name'][:52]}")

        # Find source text
        text = ""
        for src in sig.get("sources", []):
            t = text_index.get(src.get("report", ""), "")
            if t:
                text = t
                break

        result = tag_signal(client, sig, text)

        if result:
            for s in cosmos["signals"]:
                if s["id"] == sig["id"]:
                    s["horizon"] = result["horizon"]
                    if result["horizonYear"]:
                        s["horizonYear"] = result["horizonYear"]
                    elif "horizonYear" in s and not args.force:
                        pass  # keep existing if not forcing
                    break
            h = result["horizon"]
            yr = result.get("horizonYear") or ""
            print(f"    → {h}  {yr}")
            if h == "near":   near   += 1
            elif h == "medium": medium += 1
            else:               far   += 1
        else:
            errors += 1

        # Checkpoint every 25 signals
        if (i + 1) % 25 == 0:
            with open(COSMOS_PATH, "w") as f:
                json.dump(cosmos, f, indent=2)
            print(f"  💾 checkpoint ({i+1} processed)")
            time.sleep(0.5)

    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print(f"\n✓ Done.")
    print(f"  near: {near}  medium: {medium}  far: {far}  errors: {errors}")
    print(f"  cosmos.json updated at {COSMOS_PATH}")


if __name__ == "__main__":
    main()
