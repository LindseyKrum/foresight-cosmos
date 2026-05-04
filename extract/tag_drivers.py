#!/usr/bin/env python3
"""
Foresight Cosmos — Narrative driver tagger.

Tags each signal and trend with the underlying macro-force(s) driving it.
Seven canonical drivers; each signal gets 1–2.

Drivers:
  technological-acceleration
  demographic-shift
  geopolitical-fragmentation
  resource-environmental-pressure
  economic-realignment
  cultural-reorientation
  governance-regulatory-change

Usage:
  python tag_drivers.py
"""

import json
import re
from pathlib import Path

COSMOS_PATH = Path("../data/cosmos.json")

DRIVERS = [
    ("technological-acceleration", "Technological Acceleration", [
        "ai", "artificial intelligence", "machine learning", "automation",
        "digital", "compute", "algorithm", "generative", "llm", "model",
        "blockchain", "crypto", "quantum", "metaverse", "spatial computing",
        "augmented reality", "virtual reality", "platform", "data", "software",
        "infrastructure", "tech", "innovation", "robotics", "iot", "5g",
        "semiconductor", "gpu", "chip", "foundation model", "agentic",
    ]),
    ("demographic-shift", "Demographic Shift", [
        "gen z", "millennial", "boomer", "aging", "population", "youth",
        "generation", "demographic", "age", "young", "older adult",
        "family", "birth rate", "longevity", "ageing", "senior", "teen",
        "child", "adolescent", "workforce age", "grey", "silver economy",
    ]),
    ("geopolitical-fragmentation", "Geopolitical Fragmentation", [
        "geopolit", "trade war", "tariff", "sanction", "fragmentation",
        "multipolarity", "nation state", "conflict", "war", "military",
        "reshoring", "supply chain", "deglobalization", "china", "us-china",
        "russia", "ukraine", "middle east", "global south", "polycrisis",
        "sovereignty", "election", "democracy", "authoritarianism", "populism",
        "instability", "tension", "rivalry",
    ]),
    ("resource-environmental-pressure", "Resource & Environmental Pressure", [
        "climate", "carbon", "sustainability", "renewable", "energy",
        "food", "water", "biodiversity", "deforestation", "emissions",
        "net zero", "green", "electric vehicle", "ev ", "solar", "wind",
        "circular economy", "waste", "plastic", "pollution", "drought",
        "flood", "extreme weather", "temperature", "ecosystem", "nature",
        "agriculture", "hunger", "food insecurity", "resource",
    ]),
    ("economic-realignment", "Economic Realignment", [
        "inflation", "recession", "interest rate", "cost of living",
        "inequality", "wealth", "income", "economic", "gdp", "growth",
        "financial", "market", "investment", "capital", "debt", "credit",
        "fiscal", "monetary", "spending", "consumer spending", "savings",
        "trade", "export", "import", "currency", "dollar", "bank",
        "startup", "venture", "ipo", "m&a", "private equity",
    ]),
    ("cultural-reorientation", "Cultural Reorientation", [
        "identity", "values", "meaning", "community", "purpose", "wellbeing",
        "mental health", "loneliness", "belonging", "authenticity",
        "simplicity", "burnout", "lifestyle", "nostalgia", "analog",
        "craft", "human", "connection", "social", "culture", "creativity",
        "aesthetics", "spirituality", "self-care", "mindfulness",
        "trust", "status", "luxury", "experience", "joy", "happiness",
    ]),
    ("governance-regulatory-change", "Governance & Regulatory Change", [
        "regulation", "policy", "law", "governance", "compliance",
        "legal", "legislation", "regulator", "government", "government policy",
        "framework", "standard", "rule", "rights", "privacy law",
        "antitrust", "liability", "accountability", "transparency",
        "gdpr", "data protection", "audit", "oversight", "enforcement",
        "court", "treaty", "agreement", "directive",
    ]),
]


def score_text(text: str, keywords: list) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def assign_drivers(text: str) -> list[str]:
    scores = []
    for did, dname, keywords in DRIVERS:
        s = score_text(text, keywords)
        if s > 0:
            scores.append((s, did))
    scores.sort(reverse=True)
    # Return top 2 if there's a meaningful second
    if not scores:
        return ["cultural-reorientation"]  # fallback
    top = [scores[0][1]]
    if len(scores) > 1 and scores[1][0] >= max(1, scores[0][0] * 0.4):
        top.append(scores[1][1])
    return top


def main():
    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)

    driver_counts = {did: 0 for did, *_ in DRIVERS}

    for sig in cosmos["signals"]:
        text = f"{sig['name']} {sig['description']}"
        drivers = assign_drivers(text)
        sig["drivers"] = drivers
        for d in drivers:
            driver_counts[d] += 1

    for trend in cosmos["trends"]:
        text = f"{trend['name']} {trend['description']}"
        drivers = assign_drivers(text)
        trend["drivers"] = drivers

    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print("Driver distribution across signals:")
    for did, dname, _ in DRIVERS:
        bar = "█" * round(driver_counts[did] / 3)
        print(f"  {driver_counts[did]:3d}  {bar:<30} {dname}")

    print(f"\n✓ cosmos.json updated with driver tags.")


if __name__ == "__main__":
    main()
