#!/usr/bin/env python3
"""
Foresight Cosmos — PDF extraction pipeline.

Usage:
  python extract.py --pdfs ../pdfs --out ../data/cosmos.json

Drop all PDFs from both Google Drive folders into ../pdfs/ before running.
Re-run whenever new reports are added — it merges incrementally.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
import fitz  # PyMuPDF
from tqdm import tqdm

# ── Config ───────────────────────────────────────────────────────────────────
CURRENT_YEAR   = datetime.now().year
MAX_CHUNK_CHARS = 12_000   # chars per Claude call (stays within context)
MODEL           = "claude-opus-4-7"

EXTRACT_PROMPT = """You are analyzing a section of a foresight trend report.

Extract the following structured entities from this text. Be precise and concise.

Return ONLY valid JSON in this exact shape:
{
  "trends": [
    {
      "name": "Short name (3-6 words)",
      "description": "One or two declarative sentences. No fluff.",
      "confidence": 0.0-1.0
    }
  ],
  "signals": [
    {
      "name": "Short name (3-6 words)",
      "description": "One or two declarative sentences. No fluff.",
      "confidence": 0.0-1.0
    }
  ],
  "scenarios": [
    {
      "name": "Short scenario name",
      "description": "Two to four sentences describing the scenario world.",
      "confidence": 0.0-1.0
    }
  ]
}

Definitions:
- TREND: A large, sustained directional shift observable across multiple sectors over 3-10+ years.
- SIGNAL: A weak, early, or emergent indicator — a specific observation, technology, behavior, or event that points toward a possible future.
- SCENARIO: A named future state or narrative described in the report.

If a category has nothing, return an empty array. Return ONLY the JSON object, no prose.

REPORT TEXT:
"""

MERGE_PROMPT = """You are consolidating extracted foresight data from ~{n} PDF reports into a clean, deduplicated knowledge graph.

You will receive arrays of raw extracted trends, signals, and scenarios. Your job:
1. Deduplicate entries that describe the same concept (merge them, keep the best name/description).
2. Assign stable IDs: trends get t001, t002... signals get s001, s002... scenarios get sc001, sc002...
3. For each signal, identify which trends it connects to (by trend ID). A signal can connect to 1-3 trends.
4. For each scenario, identify its parent trend (by trend ID).
5. Estimate strength (0.0-1.0) for signals based on how many reports mentioned something similar.
6. Estimate mass (1.0-2.5) for trends based on how many signals connect to them and how many reports mentioned them.

Return ONLY valid JSON in this exact shape:
{
  "signals": [
    {
      "id": "s001",
      "name": "...",
      "description": "...",
      "sources": [{"report": "...", "year": 2024, "url": ""}],
      "firstSeen": 2024,
      "lastSeen": 2025,
      "strength": 0.0-1.0,
      "connections": ["t001", "t002"]
    }
  ],
  "trends": [
    {
      "id": "t001",
      "name": "...",
      "description": "...",
      "sources": [{"report": "...", "year": 2024, "url": ""}],
      "signals": ["s001", "s002"],
      "scenarios": ["sc001"],
      "firstSeen": 2024,
      "lastSeen": 2025,
      "mass": 1.0-2.5
    }
  ],
  "scenarios": [
    {
      "id": "sc001",
      "name": "...",
      "description": "...",
      "trend": "t001",
      "sources": [{"report": "...", "year": 2024, "url": ""}]
    }
  ]
}

RAW EXTRACTED DATA:
"""


# ── PDF helpers ───────────────────────────────────────────────────────────────
def extract_year_from_filename(name: str) -> int:
    """Best-effort year extraction from filename."""
    m = re.search(r'20(2[0-9])', name)
    return int(m.group(0)) if m else CURRENT_YEAR


def pdf_to_chunks(pdf_path: Path, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Extract text from PDF and split into chunks."""
    doc  = fitz.open(str(pdf_path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()

    # Clean up
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    chunks = []
    while len(text) > max_chars:
        cut = text.rfind('\n', 0, max_chars)
        if cut == -1:
            cut = max_chars
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


# ── Extraction ────────────────────────────────────────────────────────────────
def extract_from_pdf(client: anthropic.Anthropic, pdf_path: Path) -> dict:
    """Run extraction on a single PDF, returning raw entities."""
    name   = pdf_path.stem
    year   = extract_year_from_filename(name)
    chunks = pdf_to_chunks(pdf_path)

    all_trends    = []
    all_signals   = []
    all_scenarios = []

    for chunk in chunks:
        if len(chunk.strip()) < 200:
            continue
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": EXTRACT_PROMPT + chunk}],
            )
            raw  = msg.content[0].text.strip()
            # Strip markdown code fences if present
            raw  = re.sub(r'^```(?:json)?\n?', '', raw)
            raw  = re.sub(r'\n?```$', '', raw)
            parsed = json.loads(raw)
            all_trends    += parsed.get("trends",    [])
            all_signals   += parsed.get("signals",   [])
            all_scenarios += parsed.get("scenarios", [])
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"  ⚠ parse error in {name}: {e}", file=sys.stderr)
            continue

    return {
        "report": name,
        "year":   year,
        "trends":    all_trends,
        "signals":   all_signals,
        "scenarios": all_scenarios,
    }


# ── Merge / consolidate ───────────────────────────────────────────────────────
def consolidate(client: anthropic.Anthropic, raw_reports: list[dict]) -> dict:
    """Send all raw data to Claude for deduplication and graph construction."""
    payload = json.dumps(raw_reports, indent=2)

    # If payload is very large, truncate per-report to avoid token limits
    if len(payload) > 80_000:
        # Summarise to first 20 items per category per report
        trimmed = []
        for r in raw_reports:
            trimmed.append({
                "report":    r["report"],
                "year":      r["year"],
                "trends":    r["trends"][:20],
                "signals":   r["signals"][:20],
                "scenarios": r["scenarios"][:10],
            })
        payload = json.dumps(trimmed, indent=2)

    prompt = MERGE_PROMPT.format(n=len(raw_reports)) + payload

    msg = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r'^```(?:json)?\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    return json.loads(raw)


# ── Incremental merge ─────────────────────────────────────────────────────────
def load_existing(out_path: Path) -> dict | None:
    if out_path.exists():
        with open(out_path) as f:
            return json.load(f)
    return None


def already_processed(existing: dict | None, report_name: str) -> bool:
    if not existing:
        return False
    all_sources = (
        [s for sig in existing.get("signals", []) for s in sig.get("sources", [])] +
        [s for t in existing.get("trends", [])   for s in t.get("sources", [])]
    )
    return any(s["report"] == report_name for s in all_sources)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Extract foresight data from PDFs")
    parser.add_argument("--pdfs", default="../pdfs",        help="Folder of PDFs")
    parser.add_argument("--out",  default="../data/cosmos.json", help="Output JSON path")
    parser.add_argument("--api-key", default=None,          help="Anthropic API key (or set ANTHROPIC_API_KEY)")
    parser.add_argument("--force",   action="store_true",   help="Re-process all PDFs, ignore cache")
    args = parser.parse_args()

    pdf_dir  = Path(args.pdfs)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {pdf_dir}. Download from Google Drive and drop them there.")
        sys.exit(1)
    print(f"Found {len(pdfs)} PDFs.")

    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY env var or pass --api-key.")
        sys.exit(1)

    client   = anthropic.Anthropic(api_key=api_key)
    existing = None if args.force else load_existing(out_path)

    # ── Extract phase ──
    raw_reports = []
    for pdf in tqdm(pdfs, desc="Extracting PDFs"):
        name = pdf.stem
        if not args.force and already_processed(existing, name):
            print(f"  skip (already in cosmos): {name}")
            continue
        print(f"  extracting: {name}")
        result = extract_from_pdf(client, pdf)
        raw_reports.append(result)

    if not raw_reports:
        print("Nothing new to process. Use --force to reprocess all PDFs.")
        sys.exit(0)

    # If we have existing data, include it as a "report" so Claude can merge it
    if existing and not args.force:
        print(f"Merging {len(raw_reports)} new report(s) into existing cosmos...")
        raw_reports.append({
            "report":    "__existing__",
            "year":      CURRENT_YEAR,
            "trends":    [{"name": t["name"], "description": t["description"]} for t in existing.get("trends", [])],
            "signals":   [{"name": s["name"], "description": s["description"]} for s in existing.get("signals", [])],
            "scenarios": [{"name": sc["name"], "description": sc["description"]} for sc in existing.get("scenarios", [])],
        })

    # ── Consolidation phase ──
    print(f"\nConsolidating {len(raw_reports)} report extracts with Claude...")
    graph = consolidate(client, raw_reports)

    # ── Build year range from sources ──
    all_years = [
        s["year"]
        for collection in [graph.get("signals", []), graph.get("trends", []), graph.get("scenarios", [])]
        for item in collection
        for s in item.get("sources", [])
        if s.get("year")
    ]

    output = {
        "meta": {
            "generated":   datetime.now().isoformat()[:10],
            "reportCount": len(pdfs),
            "yearRange":   [min(all_years, default=CURRENT_YEAR), max(all_years, default=CURRENT_YEAR)],
        },
        "signals":   graph.get("signals",   []),
        "trends":    graph.get("trends",    []),
        "scenarios": graph.get("scenarios", []),
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ cosmos.json written to {out_path}")
    print(f"  {len(output['signals'])} signals · {len(output['trends'])} trends · {len(output['scenarios'])} scenarios")


if __name__ == "__main__":
    main()
