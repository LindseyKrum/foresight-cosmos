#!/usr/bin/env python3
"""
Foresight Cosmos — Signal merger.

Reads merge_approvals.json (a list of signal ID groups to merge),
collapses each group into a single signal, and rebuilds cosmos.json.

For each merged group:
  • Keeps the name / description of the signal with highest strength
  • Combines all sources (deduplicated by org)
  • Sets firstSeen = min, lastSeen = max across group
  • Boosts strength proportionally to source count (max 1.0)
  • Adds mergeCount field so the visualiser can scale star size

Usage:
  1. Edit merge_approvals.json (list of [sid, sid, ...] groups)
  2. python merge_signals.py

merge_approvals.json format:
[
  ["s001", "s002"],           // merge these two
  ["s010", "s011", "s012"]   // merge these three
]
"""

import json
from pathlib import Path

COSMOS_PATH    = Path("../data/cosmos.json")
APPROVALS_PATH = Path("../data/merge_approvals.json")


def merge_group(signals: list, group_ids: list) -> dict | None:
    sig_map = {s["id"]: s for s in signals}
    group   = [sig_map[sid] for sid in group_ids if sid in sig_map]
    if len(group) < 2:
        print(f"  ⚠  Group {group_ids} — could not find all signals, skipping")
        return None

    # Primary = highest strength (or most recent if tied)
    primary = max(group, key=lambda s: (s.get("strength", 0.6), s.get("lastSeen", 0)))

    # Combine sources (dedup by org+report)
    seen_reports = set()
    combined_sources = []
    for s in group:
        for src in s.get("sources", []):
            key = src.get("report", "") + "|" + str(src.get("year", ""))
            if key not in seen_reports:
                seen_reports.add(key)
                combined_sources.append(src)

    # Date range across group
    first_seen = min(s.get("firstSeen", 2025) for s in group)
    last_seen  = max(s.get("lastSeen",  2025) for s in group)

    # Strength boost: each additional source adds 0.1, capped at 1.0
    extra       = len(combined_sources) - 1
    new_strength = round(min(1.0, primary.get("strength", 0.6) + extra * 0.08), 2)

    # Union all connections
    all_connections = list({c for s in group for c in s.get("connections", [])})

    # Merge drivers (union)
    all_drivers = list({d for s in group for d in s.get("drivers", [])})

    # Tensions: keep from primary, remap IDs that were merged away
    tensions = primary.get("tensions", [])

    merged = {
        **primary,
        "sources":     combined_sources,
        "firstSeen":   first_seen,
        "lastSeen":    last_seen,
        "strength":    new_strength,
        "connections": all_connections,
        "drivers":     all_drivers,
        "tensions":    tensions,
        "mergeCount":  len(group),
        "mergedFrom":  [s["id"] for s in group if s["id"] != primary["id"]],
    }
    return merged


def main():
    if not APPROVALS_PATH.exists():
        print(f"⚠  {APPROVALS_PATH} not found.")
        print("   Create it with a JSON array of ID groups, e.g.:")
        print('   [["s001","s002"], ["s010","s011"]]')
        return

    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)
    with open(APPROVALS_PATH) as f:
        approvals = json.load(f)

    signals = cosmos["signals"]
    trends  = cosmos["trends"]

    # Track which IDs get absorbed (removed)
    absorbed_ids: set[str] = set()
    replacements: dict[str, str] = {}  # old_id → new_id (primary)

    new_signals = list(signals)  # will mutate

    for group_ids in approvals:
        merged = merge_group(signals, group_ids)
        if not merged:
            continue

        primary_id = merged["id"]
        removed    = [sid for sid in group_ids if sid != primary_id]

        # Replace primary signal in list
        for i, s in enumerate(new_signals):
            if s["id"] == primary_id:
                new_signals[i] = merged
                break

        # Remove absorbed signals
        absorbed_ids.update(removed)
        for sid in removed:
            replacements[sid] = primary_id

        print(f"  ✓ Merged {group_ids} → {primary_id}  (strength {merged['strength']}, {len(merged['sources'])} sources)")

    # Filter out absorbed signals
    new_signals = [s for s in new_signals if s["id"] not in absorbed_ids]

    # Fix any tension links pointing to absorbed IDs
    for sig in new_signals:
        sig["tensions"] = [
            {**t, "signal": replacements.get(t["signal"], t["signal"])}
            for t in sig.get("tensions", [])
            if replacements.get(t["signal"], t["signal"]) != sig["id"]
        ]

    # Rebuild trend signal registries
    for trend in trends:
        old_sigs = trend.get("signals", [])
        new_sigs = []
        for sid in old_sigs:
            mapped = replacements.get(sid, sid)
            if mapped not in absorbed_ids and mapped not in new_sigs:
                new_sigs.append(mapped)
        trend["signals"] = new_sigs
        # Recalculate mass
        sig_count = len(new_sigs)
        sc_count  = len(trend.get("scenarios", []))
        trend["mass"] = round(min(2.5, 1.0 + sig_count * 0.3 + sc_count * 0.2), 2)

    cosmos["signals"] = new_signals
    cosmos["trends"]  = trends

    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print(f"\n✓ cosmos.json updated.")
    print(f"  {len(signals)} → {len(new_signals)} signals ({len(absorbed_ids)} merged away)")


if __name__ == "__main__":
    main()
