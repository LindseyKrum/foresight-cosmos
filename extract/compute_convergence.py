#!/usr/bin/env python3
"""
Foresight Cosmos — Convergence scorer.

For each macro-planet (trend), calculates:
  • convergenceScore  — 0–1, fraction of org-type categories represented
  • orgTypeBreakdown  — {orgType: count} dict of contributing org types
  • convergenceLabel  — "Niche" / "Emerging" / "Cross-sector" / "Universal"

A signal is universally convergent when Financial, Consultancy, Agency,
Research, Tech, and at least one of Industry / Government / UN & IGO / Media
all independently flag the same theme.

Usage:
  python compute_convergence.py
"""

import json
from pathlib import Path
from collections import Counter

COSMOS_PATH = Path("../data/cosmos.json")

ALL_ORG_TYPES = [
    "Consultancy",
    "Financial",
    "Agency",
    "Research",
    "Tech",
    "Industry",
    "Government",
    "UN & IGO",
    "Media",
]


def convergence_label(score: float) -> str:
    if score < 0.25:
        return "Niche"
    if score < 0.45:
        return "Emerging"
    if score < 0.70:
        return "Cross-sector"
    return "Universal"


def main():
    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)

    sig_map = {s["id"]: s for s in cosmos["signals"]}

    for trend in cosmos["trends"]:
        type_counts: Counter = Counter()

        for sid in trend.get("signals", []):
            sig = sig_map.get(sid)
            if not sig:
                continue
            for src in sig.get("sources", []):
                ot = src.get("orgType")
                if ot:
                    type_counts[ot] += 1

        distinct = len(type_counts)
        score    = round(distinct / len(ALL_ORG_TYPES), 3)
        label    = convergence_label(score)

        trend["convergenceScore"]   = score
        trend["convergenceLabel"]   = label
        trend["orgTypeBreakdown"]   = dict(type_counts)

    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print("Convergence scores:")
    for t in sorted(cosmos["trends"], key=lambda x: -x["convergenceScore"]):
        bar = "█" * round(t["convergenceScore"] * 20)
        print(f"  {t['convergenceScore']:.2f} {bar:<20} [{t['convergenceLabel']:<12}] {t['name'][:50]}")

    print(f"\n✓ cosmos.json updated with convergence data.")


if __name__ == "__main__":
    main()
