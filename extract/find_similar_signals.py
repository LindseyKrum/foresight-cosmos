#!/usr/bin/env python3
"""
Foresight Cosmos — Signal similarity finder.

Computes pairwise name similarity across all signals, clusters near-duplicates,
and writes a review file (signal_clusters.json) for human approval.

Similarity method: Jaccard on significant word sets from the signal name,
with a secondary boost if descriptions also overlap heavily.

Usage:
  python find_similar_signals.py
  → writes ../data/signal_clusters.json
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from itertools import combinations

COSMOS_PATH   = Path("../data/cosmos.json")
CLUSTERS_PATH = Path("../data/signal_clusters.json")

STOPWORDS = {
    "the","and","for","with","from","into","that","this","are","has","have",
    "been","being","will","would","could","should","more","also","their",
    "they","than","then","when","what","which","about","over","under","both",
    "each","most","some","such","very","just","but","not","all","new","its",
    "via","per","across","within","between","through","while","where","even",
    "amid","into","as","at","by","in","on","of","to","an","a","is","it",
    "up","out","off","so","do","be","can","may","was","use","used","using",
    "towards","against","without","among","along",
}

NAME_WEIGHT    = 3   # name words count 3× vs description words
SIM_THRESHOLD  = 0.38


def tokenise(text: str, weight: int = 1) -> list[str]:
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    return [w for w in words if w not in STOPWORDS] * weight


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def similarity(s1: dict, s2: dict) -> float:
    name_words1 = set(tokenise(s1["name"], NAME_WEIGHT))
    name_words2 = set(tokenise(s2["name"], NAME_WEIGHT))
    desc_words1 = set(tokenise(s1.get("description", "")))
    desc_words2 = set(tokenise(s2.get("description", "")))

    name_sim = jaccard(name_words1, name_words2)
    desc_sim = jaccard(desc_words1, desc_words2)

    # Weighted: name matters 3×, description 1×
    return (name_sim * 3 + desc_sim) / 4


def cluster_signals(signals: list) -> list:
    """Return list of clusters; each cluster is a list of signal dicts."""
    n = len(signals)
    # Build adjacency: pairs above threshold
    adj = defaultdict(set)
    scores = {}

    print(f"Computing pairwise similarity for {n} signals...")
    for i, j in combinations(range(n), 2):
        sim = similarity(signals[i], signals[j])
        if sim >= SIM_THRESHOLD:
            adj[i].add(j)
            adj[j].add(i)
            scores[(min(i,j), max(i,j))] = round(sim, 3)

    # Union-find clustering
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i, neighbours in adj.items():
        for j in neighbours:
            union(i, j)

    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    clusters = []
    for root, members in groups.items():
        if len(members) < 2:
            continue
        cluster_sigs = [signals[i] for i in members]
        # Compute average pairwise score for the cluster
        pair_scores = [
            scores.get((min(i,j), max(i,j)), 0)
            for i, j in combinations(members, 2)
        ]
        avg_score = round(sum(pair_scores) / len(pair_scores), 3) if pair_scores else 0
        clusters.append({
            "avgSimilarity": avg_score,
            "signals": [
                {
                    "id":          s["id"],
                    "name":        s["name"],
                    "description": s["description"],
                    "sources":     [src.get("org", src.get("report","")) for src in s.get("sources",[])],
                    "strength":    s.get("strength", 0.6),
                    "firstSeen":   s.get("firstSeen"),
                    "lastSeen":    s.get("lastSeen"),
                }
                for s in cluster_sigs
            ],
        })

    clusters.sort(key=lambda c: -c["avgSimilarity"])
    return clusters


def main():
    with open(COSMOS_PATH) as f:
        cosmos = json.load(f)

    signals  = cosmos["signals"]
    clusters = cluster_signals(signals)

    # Split into strong (likely duplicates) and moderate (review)
    strong   = [c for c in clusters if c["avgSimilarity"] >= 0.52]
    moderate = [c for c in clusters if 0.38 <= c["avgSimilarity"] < 0.52]

    output = {
        "meta": {
            "totalSignals":    len(signals),
            "clustersFound":   len(clusters),
            "strongDuplicates": len(strong),
            "moderateMatches": len(moderate),
        },
        "strong":   strong,
        "moderate": moderate,
    }

    with open(CLUSTERS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'─'*60}")
    print(f"Strong duplicates ({len(strong)} clusters):")
    for c in strong[:20]:
        print(f"\n  [{c['avgSimilarity']:.2f}]")
        for s in c["signals"]:
            orgs = ", ".join(s["sources"][:2])
            print(f"    • {s['name'][:60]}")
            print(f"      ({orgs})")

    print(f"\n{'─'*60}")
    print(f"Moderate matches ({len(moderate)} clusters — first 10):")
    for c in moderate[:10]:
        print(f"\n  [{c['avgSimilarity']:.2f}]")
        for s in c["signals"]:
            orgs = ", ".join(s["sources"][:2])
            print(f"    • {s['name'][:60]}")
            print(f"      ({orgs})")

    print(f"\n✓ Full results written to {CLUSTERS_PATH}")
    print(f"  {len(clusters)} total clusters across {sum(len(c['signals']) for c in clusters)} signals")


if __name__ == "__main__":
    main()
