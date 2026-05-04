#!/usr/bin/env python3
"""
Foresight Cosmos — Tension mapper.

Finds signal pairs that sit in conceptual opposition — where two signals
describe forces pulling in opposite directions. Stores up to 2 tension
links per signal as { "signal": sid, "label": "..." }.

Tension archetypes detected:
  • AI productivity  ↔  AI job displacement
  • Sustainability   ↔  Greenwashing / ESG backlash
  • Digital connection ↔ Loneliness / social isolation
  • Centralisation   ↔  Decentralisation / Web3
  • Privacy          ↔  Data monetisation
  • Growth optimism  ↔  Recession / contraction
  • Luxury expansion ↔  Dupe / resale / frugality
  • Human creativity ↔  AI-generated content
  • Globalisation    ↔  Deglobalisation / reshoring
  • Wellness trend   ↔  Burnout / overwork

Usage:
  python find_tensions.py
"""

import json
from pathlib import Path

COSMOS_PATH = Path("../data/cosmos.json")

# Each archetype: (label, pole_A_keywords, pole_B_keywords)
TENSION_ARCHETYPES = [
    (
        "AI productivity vs. job displacement",
        ["productivity", "efficiency", "automation benefit", "ai workflow", "ai tool", "ai boost"],
        ["job loss", "displacement", "unemployment", "workforce reduction", "replaced by ai", "layoff", "reskilling"],
    ),
    (
        "Sustainability commitment vs. ESG backlash",
        ["net zero", "sustainability target", "esg", "climate commitment", "green pledge", "decarbonization"],
        ["esg backlash", "greenwashing", "esg retreat", "anti-esg", "sustainability fatigue", "esg sceptic"],
    ),
    (
        "Digital connection vs. social isolation",
        ["digital community", "social platform", "online connection", "social media growth", "digital social"],
        ["loneliness", "social isolation", "disconnection", "offline", "screen fatigue", "digital detox"],
    ),
    (
        "Centralisation (big tech) vs. decentralisation (web3)",
        ["big tech", "platform monopoly", "centralised", "cloud giant", "tech consolidation"],
        ["decentralised", "blockchain", "web3", "defi", "crypto", "peer-to-peer", "tokenisation"],
    ),
    (
        "Privacy rights vs. data monetisation",
        ["privacy", "data protection", "gdpr", "right to erasure", "consent", "privacy-first"],
        ["data monetisation", "data brokerage", "surveillance", "tracking", "ad targeting", "data harvesting"],
    ),
    (
        "Economic optimism vs. contraction risk",
        ["growth", "recovery", "expansion", "bull market", "consumer confidence", "optimism", "soft landing"],
        ["recession", "contraction", "downturn", "bear market", "declining", "slowdown", "cost-cutting"],
    ),
    (
        "Luxury growth vs. dupe / frugality culture",
        ["luxury growth", "premium", "high-end", "ultra-luxury", "luxury spending", "affluent"],
        ["dupe", "frugality", "resale", "secondhand", "affordable", "value-seeking", "budget", "cost of living"],
    ),
    (
        "Human creativity vs. AI-generated content",
        ["human creativity", "handmade", "craft", "artisanal", "made by humans", "authentic creation"],
        ["ai-generated", "generative ai content", "ai art", "synthetic media", "deepfake", "ai writing"],
    ),
    (
        "Globalisation vs. deglobalisation",
        ["global trade", "globalisation", "international supply chain", "cross-border", "free trade"],
        ["deglobalisation", "reshoring", "nearshoring", "trade war", "tariff", "fragmentation", "protectionism"],
    ),
    (
        "Wellness optimism vs. burnout reality",
        ["wellness", "self-care", "wellbeing trend", "mental health investment", "mindfulness"],
        ["burnout", "exhaustion", "overwork", "hustle culture", "stress epidemic", "always-on"],
    ),
    (
        "AI regulation vs. AI acceleration",
        ["ai regulation", "ai governance", "ai safety", "ai oversight", "responsible ai", "ai law"],
        ["ai acceleration", "move fast", "ai arms race", "deregulation", "light-touch", "ai investment surge"],
    ),
    (
        "Brand purpose vs. purpose fatigue",
        ["brand purpose", "purpose-led", "values-driven brand", "social responsibility", "mission-driven"],
        ["purpose fatigue", "purpose washing", "consumers distrust brands", "brand scepticism", "brand backlash"],
    ),
]


def score(text: str, keywords: list) -> int:
    tl = text.lower()
    return sum(1 for kw in keywords if kw in tl)


def main():
    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)

    signals = cosmos["signals"]

    # Build per-signal pole scores
    # poles[sid] = [(archetype_label, pole, score), ...]
    poles = {s["id"]: [] for s in signals}
    for sig in signals:
        text = f"{sig['name']} {sig['description']}"
        for label, kw_a, kw_b in TENSION_ARCHETYPES:
            sa = score(text, kw_a)
            sb = score(text, kw_b)
            if sa >= 1:
                poles[sig["id"]].append((label, "A", sa))
            if sb >= 1:
                poles[sig["id"]].append((label, "B", sb))

    # Find pairs: same archetype label, opposite poles
    from collections import defaultdict
    archetype_pole: dict = defaultdict(lambda: {"A": [], "B": []})
    for sid, entries in poles.items():
        for label, pole, sc in entries:
            archetype_pole[label][pole].append((sc, sid))

    # Build tensions dict: sid -> [(other_sid, label)]
    tensions: dict = defaultdict(list)
    pair_count = 0
    for label, sides in archetype_pole.items():
        a_sigs = sorted(sides["A"], reverse=True)[:6]  # top 6 on each pole
        b_sigs = sorted(sides["B"], reverse=True)[:6]
        if not a_sigs or not b_sigs:
            continue
        # Create cross-pairs (top 3 A × top 3 B)
        for sc_a, sid_a in a_sigs[:3]:
            for sc_b, sid_b in b_sigs[:3]:
                if sid_a == sid_b:
                    continue
                tensions[sid_a].append({"signal": sid_b, "label": label})
                tensions[sid_b].append({"signal": sid_a, "label": label})
                pair_count += 1

    # Deduplicate and cap at 2 per signal
    for sig in signals:
        seen_labels = set()
        deduped = []
        for t in tensions.get(sig["id"], []):
            if t["label"] not in seen_labels and len(deduped) < 2:
                deduped.append(t)
                seen_labels.add(t["label"])
        sig["tensions"] = deduped

    cosmos["signals"] = signals
    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print(f"Tension archetypes processed: {len(TENSION_ARCHETYPES)}")
    print(f"Tension pairs created:        {pair_count}")

    tension_counts = sum(1 for s in signals if s.get("tensions"))
    print(f"Signals with tensions:        {tension_counts} / {len(signals)}")

    # Show a sample
    print("\nSample tensions:")
    sig_map = {s["id"]: s for s in signals}
    shown = 0
    for sig in signals:
        for t in sig.get("tensions", []):
            other = sig_map.get(t["signal"])
            if other and shown < 8:
                print(f"  ↔ {sig['name'][:45]:<45}")
                print(f"    {other['name'][:45]:<45}")
                print(f"    [{t['label']}]")
                print()
                shown += 1
                break

    print("✓ cosmos.json updated with tension links.")


if __name__ == "__main__":
    main()
