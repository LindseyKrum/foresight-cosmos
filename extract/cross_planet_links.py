#!/usr/bin/env python3
"""
Foresight Cosmos — Cross-planet signal linker.
Analyses each signal's name + description for relevance to multiple
macro-planets. Adds secondary connections where a signal clearly
spans more than one theme.

Usage:
  python cross_planet_links.py
"""

import json
import re
from pathlib import Path
from collections import defaultdict

COSMOS_PATH = Path("../data/cosmos.json")

# ── Keyword sets per planet ID ────────────────────────────────────────────────
# Each tuple: (planet_id, planet_name, [keywords])
PLANET_KEYWORDS = [
    ("t001", "AI: Infrastructure, Capability & Governance", [
        "artificial intelligence", "generative ai", "large language model", "llm",
        "foundation model", "gpu", "compute", "inference", "training", "openai",
        "anthropic", "ai governance", "ai regulation", "ai alignment", "ai safety",
        "ai infrastructure", "agentic", "multimodal", "model architecture",
        "ai boom", "ai investment", "ai arms race",
    ]),
    ("t002", "Cybersecurity & Data", [
        "cybersecurity", "cyber security", "data breach", "privacy", "encryption",
        "quantum cryptography", "zero trust", "ransomware", "data governance",
        "data protection", "gdpr", "cookie", "traceability", "security threat",
        "cyber resilience", "data litigation",
    ]),
    ("t003", "AI in Business & Work", [
        "enterprise ai", "business ai", "ai adoption", "ai workflow",
        "ai productivity", "ai roi", "automation", "knowledge work",
        "ai deployment", "b2b", "sales", "legal ai", "ai operations",
        "workforce ai", "ai tools", "ai talent",
    ]),
    ("t004", "AI in Creativity & Culture", [
        "creative ai", "ai creativity", "generative art", "ai-generated",
        "ai content", "ai design", "ai music", "ai writing", "ai culture",
        "human creativity", "made by humans", "ai aesthetics", "algorithmic",
        "ai art", "empathetic ai", "ai identity",
    ]),
    ("t005", "Creator Economy & Social Media", [
        "creator economy", "influencer", "content creator", "social media",
        "tiktok", "youtube", "instagram", "short-form video", "ugc",
        "fandom", "social platform", "creator", "user-generated",
        "social commerce", "brand chemistry", "de-influencing",
    ]),
    ("t006", "Brand, Marketing & Advertising", [
        "brand", "marketing", "advertising", "media buying", "ad spend",
        "retail media", "ctv", "connected tv", "pr ", "public relations",
        "brand strategy", "brand equity", "campaign", "media agency",
        "measurement", "attribution", "contextual advertising",
    ]),
    ("t007", "Consumer Behavior & Identity", [
        "consumer", "consumer behavior", "consumer spending", "consumer sentiment",
        "identity", "lifestyle", "values", "purchasing", "cost of living",
        "inflation impact", "dupe", "nostalgia", "simplicity", "wellbeing consumer",
        "micro happiness", "burrowing", "generational spending",
    ]),
    ("t008", "Fashion, Luxury & Aesthetics", [
        "fashion", "luxury", "aesthetic", "beauty", "style", "design",
        "resale", "secondhand", "craftsmanship", "analog", "visual culture",
        "typography", "photography", "streetwear", "sustainable fashion",
        "surrealism", "maximalist",
    ]),
    ("t009", "Health & Medicine", [
        "health", "medicine", "medical", "clinical", "drug discovery",
        "pharmaceutical", "biotech", "glp-1", "ozempic", "femtech",
        "genomics", "patient", "healthcare", "diagnostics", "therapy",
        "vaccine", "longevity", "wearable health", "personalized medicine",
    ]),
    ("t010", "Wellbeing & Mental Health", [
        "wellbeing", "mental health", "wellness", "fitness", "burnout",
        "mindfulness", "therapy access", "social fitness", "run club",
        "strength training", "recovery", "stress", "loneliness",
        "work-life balance", "biohacking", "human energy",
    ]),
    ("t011", "Future of Work", [
        "future of work", "workplace", "remote work", "hybrid work",
        "employment", "skills gap", "reskilling", "workforce", "talent",
        "pay equity", "right to disconnect", "boundaries at work",
        "knowledge worker", "job market", "labor market",
    ]),
    ("t012", "Climate & Sustainability", [
        "climate", "sustainability", "carbon", "net zero", "renewable energy",
        "green", "ev ", "electric vehicle", "circular economy", "esg",
        "decarbonization", "clean energy", "food waste", "biodiversity",
        "climate adaptation", "sustainable", "emissions",
    ]),
    ("t013", "Geopolitics & Economic Order", [
        "geopolitics", "geopolitical", "trade war", "tariff", "reshoring",
        "multipolarity", "polycrisis", "global order", "sanctions",
        "supply chain", "deglobalization", "fragmentation", "nation state",
        "government policy", "political", "democracy", "conflict",
    ]),
    ("t014", "Financial Markets & Investment", [
        "investment", "financial markets", "interest rates", "federal reserve",
        "private equity", "credit", "bonds", "equity markets", "inflation",
        "recession", "gdp", "fiscal policy", "monetary policy", "m&a",
        "asset management", "capital markets", "venture capital",
    ]),
    ("t015", "Emerging Tech, Crypto & Web3", [
        "blockchain", "crypto", "bitcoin", "ethereum", "web3", "defi",
        "nft", "stablecoin", "tokenization", "quantum computing",
        "spatial computing", "metaverse", "augmented reality", "virtual reality",
        "iot", "5g", "digital twin", "industrial metaverse",
    ]),
    ("t016", "Food & Nutrition", [
        "food", "nutrition", "diet", "eating", "beverage", "snacking",
        "restaurant", "food system", "food insecurity", "hunger",
        "food innovation", "plant-based", "food tech", "flavor",
        "food waste", "agriculture",
    ]),
    ("t017", "Travel & Experience", [
        "travel", "tourism", "destination", "hospitality", "hotel",
        "airline", "experience economy", "live events", "experiential",
        "concert", "festival", "spectacle", "vacation",
    ]),
    ("t018", "Gaming, Entertainment & Media", [
        "gaming", "entertainment", "media", "streaming", "journalism",
        "news", "video game", "esports", "transmedia", "content platform",
        "audience", "fandom", "pop culture", "film", "television",
        "digital franchise",
    ]),
    ("t019", "Futures & Foresight", [
        "foresight", "futures", "scenario", "megatrend", "forecast",
        "uncertainty", "trend methodology", "horizon scanning",
        "strategic foresight", "systemic risk", "ontological",
        "youth foresight", "anticipatory",
    ]),
]

# Minimum keyword match score to add a secondary connection
SECONDARY_THRESHOLD = 2   # must match at least 2 keywords in a non-primary planet


def score_text(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def find_cross_planet_connections(signals: list, trends: list) -> dict:
    """Returns {signal_id: [additional_planet_ids]} for signals that span planets."""
    trend_map = {t["id"]: t for t in trends}
    additions = {}

    for sig in signals:
        text       = f"{sig['name']} {sig['description']}"
        primary    = sig["connections"][0] if sig["connections"] else None
        existing   = set(sig["connections"])

        scores = []
        for pid, pname, keywords in PLANET_KEYWORDS:
            if pid in existing:
                continue
            score = score_text(text, keywords)
            if score >= SECONDARY_THRESHOLD:
                scores.append((score, pid, pname))

        scores.sort(reverse=True)
        # Add up to 2 secondary connections
        new_connections = [pid for _, pid, _ in scores[:2]]

        if new_connections:
            additions[sig["id"]] = new_connections

    return additions


def main():
    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)

    signals = cosmos["signals"]
    trends  = cosmos["trends"]

    print(f"Analysing {len(signals)} signals for cross-planet relevance...")
    additions = find_cross_planet_connections(signals, trends)

    print(f"\nFound {len(additions)} signals with secondary connections:\n")

    sig_map = {s["id"]: s for s in signals}
    planet_map = {pid: pname for pid, pname, _ in PLANET_KEYWORDS}

    for sid, new_pids in sorted(additions.items()):
        sig = sig_map[sid]
        primary_planet = planet_map.get(sig["connections"][0], sig["connections"][0])
        new_names = [planet_map.get(p, p) for p in new_pids]
        print(f"  {sig['name'][:55]:<55}")
        print(f"    primary → {primary_planet}")
        for n in new_names:
            print(f"    also    → {n}")
        print()

    # Apply additions
    updated = 0
    for sig in signals:
        new_pids = additions.get(sig["id"], [])
        for pid in new_pids:
            if pid not in sig["connections"]:
                sig["connections"].append(pid)
                updated += 1

    # Update trend signal registries
    trend_obj_map = {t["id"]: t for t in trends}
    for sig in signals:
        for pid in sig["connections"]:
            if pid in trend_obj_map:
                if sig["id"] not in trend_obj_map[pid]["signals"]:
                    trend_obj_map[pid]["signals"].append(sig["id"])

    cosmos["signals"] = signals
    cosmos["trends"]  = trends

    with open(COSMOS_PATH, "w") as f:
        json.dump(cosmos, f, indent=2)

    print(f"\n✓ Added {updated} secondary connections across {len(additions)} signals.")
    print(f"  cosmos.json updated.")


if __name__ == "__main__":
    main()
