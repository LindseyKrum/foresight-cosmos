#!/usr/bin/env python3
"""
Foresight Cosmos — Batch result consolidator.
Reads result_00.json through result_27.json, builds cosmos.json.

Usage:
  python consolidate.py
"""

import json
import re
from pathlib import Path
from datetime import datetime

BATCHES_DIR = Path("../data/batches")
OUT_PATH    = Path("../data/cosmos.json")
CURRENT_YEAR = 2025

def slugify(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40]

def load_all_batches():
    entries = []
    for i in range(28):
        path = BATCHES_DIR / f"result_{i:02d}.json"
        if not path.exists():
            print(f"  WARNING: {path} not found, skipping")
            continue
        with open(path) as f:
            data = json.load(f)
        for entry in data.get("entries", []):
            entries.append(entry)
    return entries

def build_cosmos(entries):
    trends    = []
    signals   = []
    scenarios = []

    t_counter  = 1
    s_counter  = 1
    sc_counter = 1

    for entry in entries:
        filename = entry["filename"]
        year     = entry.get("year", CURRENT_YEAR)
        source_report = filename.replace(".pdf", "")
        org      = entry.get("org", "Unknown")
        org_type = entry.get("orgType", "Research")

        # Collect trend IDs for this entry
        entry_trend_ids = []

        for t in entry.get("trends", []):
            tid = f"t{t_counter:03d}"
            t_counter += 1
            trends.append({
                "id":          tid,
                "name":        t["name"],
                "description": t["description"],
                "sources":     [{"report": source_report, "year": year, "url": "", "org": org, "orgType": org_type}],
                "signals":     [],
                "scenarios":   [],
                "firstSeen":   year,
                "lastSeen":    year,
                "mass":        1.0,   # will be recalculated
            })
            entry_trend_ids.append(tid)

        for sig in entry.get("signals", []):
            sid = f"s{s_counter:03d}"
            s_counter += 1
            # Connect signal to trends from same entry, or first available trend
            connections = entry_trend_ids[:2] if entry_trend_ids else []
            if not connections and trends:
                connections = [trends[-1]["id"]]
            signals.append({
                "id":          sid,
                "name":        sig["name"],
                "description": sig["description"],
                "sources":     [{"report": source_report, "year": year, "url": "", "org": org, "orgType": org_type}],
                "firstSeen":   year,
                "lastSeen":    year,
                "strength":    0.6,   # default; bumped for multi-source
                "connections": connections,
            })
            # Register this signal with its connected trends
            for tid in connections:
                for tr in trends:
                    if tr["id"] == tid:
                        if sid not in tr["signals"]:
                            tr["signals"].append(sid)

        for sc in entry.get("scenarios", []):
            scid = f"sc{sc_counter:03d}"
            sc_counter += 1
            parent_trend = entry_trend_ids[0] if entry_trend_ids else (trends[-1]["id"] if trends else "t001")
            scenarios.append({
                "id":          scid,
                "name":        sc["name"],
                "description": sc["description"],
                "trend":       parent_trend,
                "sources":     [{"report": source_report, "year": year, "url": "", "org": org, "orgType": org_type}],
            })
            # Register scenario with its parent trend
            for tr in trends:
                if tr["id"] == parent_trend:
                    if scid not in tr["scenarios"]:
                        tr["scenarios"].append(scid)

    # ── Recalculate mass based on signal count ──
    for tr in trends:
        sig_count = len(tr["signals"])
        sc_count  = len(tr["scenarios"])
        # mass: 1.0 baseline, up to 2.5 for heavily connected trends
        tr["mass"] = round(min(2.5, 1.0 + sig_count * 0.3 + sc_count * 0.2), 2)

    # ── Boost strength for signals that share names/themes with others ──
    # Simple keyword overlap boost
    name_words = {}
    for sig in signals:
        words = set(re.findall(r'\b\w{4,}\b', sig["name"].lower()))
        for w in words:
            name_words.setdefault(w, []).append(sig["id"])

    boost_ids = set()
    for w, ids in name_words.items():
        if len(ids) > 1:
            boost_ids.update(ids)

    for sig in signals:
        if sig["id"] in boost_ids:
            sig["strength"] = round(min(1.0, sig["strength"] + 0.2), 2)

    return trends, signals, scenarios

def main():
    print("Loading batch results...")
    entries = load_all_batches()
    print(f"  Loaded {len(entries)} report entries")

    print("Building cosmos graph...")
    trends, signals, scenarios = build_cosmos(entries)

    # Year range
    all_years = [e.get("year", CURRENT_YEAR) for e in entries if e.get("year")]
    year_range = [min(all_years), max(all_years)] if all_years else [2023, 2025]

    output = {
        "meta": {
            "generated":   datetime.now().isoformat()[:10],
            "reportCount": len(entries),
            "yearRange":   year_range,
        },
        "signals":   signals,
        "trends":    trends,
        "scenarios": scenarios,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ cosmos.json written to {OUT_PATH}")
    print(f"  {len(signals)} signals · {len(trends)} trends · {len(scenarios)} scenarios")
    print(f"  Year range: {year_range[0]}–{year_range[1]}")
    print(f"  Report count: {len(entries)}")

if __name__ == "__main__":
    main()
