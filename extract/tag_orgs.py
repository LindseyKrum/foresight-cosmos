#!/usr/bin/env python3
"""
Foresight Cosmos — Publisher org tagger.
Reads every result_XX.json, adds `org` and `orgType` to each entry,
writes the files back in place.

Usage:
  python tag_orgs.py
"""

import json
from pathlib import Path

BATCHES_DIR = Path("../data/batches")

# ── Org type legend ──────────────────────────────────────────────────────────
# Consultancy   — Big-4, strategy & mgmt consultants, advisory firms
# Financial     — Investment banks, asset managers, private banks
# Agency        — Ad agencies, PR, creative & design studios, influencer shops
# Research      — Trend forecasters, research firms, think tanks, foresight groups
# Tech          — Tech companies, SaaS platforms, data tools
# Industry      — Brands / corporates reporting on their own sector
# Government    — Regulators, policy bodies, national agencies
# UN & IGO      — UN agencies, intergovernmental organisations
# Media         — Publishers, media companies, journalism

# Map: filename prefix (lower-case, stripped) → (org display name, orgType)
ORG_MAP = {
    "11fs pulse":                    ("11:FS",                                 "Research"),
    "2b ahead":                      ("2b AHEAD ThinkTank",                    "Research"),
    "accenture":                     ("Accenture",                             "Consultancy"),
    "acxiom":                        ("Acxiom",                                "Tech"),
    "adm":                           ("ADM",                                   "Industry"),
    "adweek":                        ("Adweek",                                "Media"),
    "aeroplane":                     ("AEROPLANE",                             "Agency"),
    "alix partners":                 ("AlixPartners",                          "Consultancy"),
    "allianz gi":                    ("Allianz Global Investors",              "Financial"),
    "allianz":                       ("Allianz",                               "Financial"),
    "amadeus":                       ("Amadeus × Globetrender",               "Industry"),
    "amundi":                        ("Amundi",                                "Financial"),
    "aptean":                        ("Aptean",                                "Tech"),
    "ark invest":                    ("ARK Invest",                            "Financial"),
    "ark_big":                       ("ARK Invest",                            "Financial"),
    "artlist":                       ("Artlist",                               "Tech"),
    "artnet":                        ("Artnet",                                "Media"),
    "aspid":                         ("Aspid",                                 "Consultancy"),
    "astrotwins":                    ("The AstroTwins",                        "Media"),
    "axa":                           ("AXA",                                   "Financial"),
    "bananas music":                 ("Bananas Music",                         "Industry"),
    "banco santander":               ("Banco Santander",                       "Financial"),
    "bank of america":               ("Bank of America",                       "Financial"),
    "barclays":                      ("Barclays",                              "Financial"),
    "basis technologies":            ("Basis Technologies",                    "Tech"),
    "berlin packaging":              ("Berlin Packaging",                      "Industry"),
    "bitcoin suisse":                ("Bitcoin Suisse",                        "Financial"),
    "blackbot":                      ("Blackbot",                              "Agency"),
    "blackrock":                     ("BlackRock",                             "Financial"),
    "bompas parr":                   ("Bompas & Parr",                        "Agency"),
    "bompas_parr":                   ("Bompas & Parr",                        "Agency"),
    "born social":                   ("Born Social",                           "Agency"),
    "british airways":               ("British Airways",                       "Industry"),
    "capgemini":                     ("Capgemini",                             "Consultancy"),
    "cassandra":                     ("Cassandra",                             "Research"),
    "cb-insights":                   ("CB Insights",                           "Research"),
    "ces":                           ("Consumer Electronics Show (CES)",       "Research"),
    "coinbase":                      ("Coinbase",                              "Tech"),
    "colin lewis":                   ("Colin Lewis",                           "Consultancy"),
    "contagious":                    ("Contagious",                            "Research"),
    "corrs":                         ("Corrs Chambers Westgarth",             "Consultancy"),
    "creator iq":                    ("Creator IQ",                            "Tech"),
    "data axle":                     ("Data Axle",                             "Tech"),
    "dataai":                        ("data.ai",                               "Tech"),
    "dcdx":                          ("DCDX",                                  "Research"),
    "deloitte":                      ("Deloitte",                              "Consultancy"),
    "dentsu creative":               ("Dentsu Creative",                       "Agency"),
    "dentsu":                        ("Dentsu",                                "Agency"),
    "determ":                        ("Determ",                                "Tech"),
    "dff":                           ("DFF",                                   "Consultancy"),
    "diageo":                        ("Diageo",                                "Industry"),
    "digital voices":                ("Digital Voices",                        "Agency"),
    "ebiquity":                      ("Ebiquity",                              "Research"),
    "econsultancy":                  ("Econsultancy",                          "Research"),
    "edelman":                       ("Edelman",                               "Agency"),
    "emarketer":                     ("eMarketer / Insider Intelligence",      "Research"),
    "epa":                           ("US EPA",                                "Government"),
    "eprs":                          ("European Parliament Research Service",  "Government"),
    "equinix":                       ("Equinix",                               "Tech"),
    "esfera":                        ("Esfera",                                "Consultancy"),
    "ey":                            ("EY (Ernst & Young)",                    "Consultancy"),
    "ezra eeman":                    ("Ezra Eeman",                            "Research"),
    "fidelity":                      ("Fidelity Investments",                  "Financial"),
    "filmsupply":                    ("Filmsupply",                            "Tech"),
    "firjan":                        ("FIRJAN",                                "Research"),
    "freshfields":                   ("Freshfields",                           "Consultancy"),
    "frog":                          ("Frog Design",                           "Agency"),
    "fti":                           ("FTI Consulting",                        "Consultancy"),
    "g7":                            ("G7",                                    "Government"),
    "gad insights":                  ("GAD Insights",                          "Research"),
    "gensler":                       ("Gensler",                               "Agency"),
    "globant":                       ("Globant",                               "Tech"),
    "goldman sachs":                 ("Goldman Sachs",                         "Financial"),
    "gp bullhound":                  ("GP Bullhound",                          "Financial"),
    "gs1":                           ("GS1",                                   "Research"),
    "hannah grey":                   ("Hannah Grey VC",                        "Financial"),
    "havas red":                     ("Havas Red",                             "Agency"),
    "hbr":                           ("Harvard Business Review",               "Media"),
    "helaba":                        ("Helaba",                                "Financial"),
    "highsnobiety":                  ("Highsnobiety",                          "Media"),
    "hilton":                        ("Hilton",                                "Industry"),
    "hmn":                           ("HMN",                                   "Media"),
    "horizon group":                 ("Horizon Group",                         "Agency"),
    "horizon media":                 ("Horizon Media",                         "Agency"),
    "house captain":                 ("House Captain",                         "Agency"),
    "hsbc":                          ("HSBC Global Private Banking",           "Financial"),
    "hubspot":                       ("HubSpot",                               "Tech"),
    "human8":                        ("Human8",                                "Research"),
    "ikea":                          ("IKEA",                                  "Industry"),
    "ilunion hotels":                ("ILUNION Hotels",                        "Industry"),
    "infosys":                       ("Infosys",                               "Tech"),
    "ing":                           ("ING",                                   "Financial"),
    "insider":                       ("Insider Intelligence",                  "Research"),
    "interbrand":                    ("Interbrand",                            "Agency"),
    "international bar association": ("International Bar Association",         "Research"),
    "international energy agency":   ("International Energy Agency",           "Government"),
    "international labour":          ("ILO",                                   "UN & IGO"),
    "intersect":                     ("Intersect",                             "Research"),
    "invesco":                       ("Invesco",                               "Financial"),
    "ipsos":                         ("Ipsos",                                 "Research"),
    "j p morgan":                    ("J.P. Morgan",                           "Financial"),
    "john lewis":                    ("John Lewis Partnership",                "Industry"),
    "juan isaza":                    ("Juan Isaza / DDB Latina",               "Agency"),
    "julius  bar":                   ("Julius Bär",                            "Financial"),
    "julius bar":                    ("Julius Bär",                            "Financial"),
    "kantar media":                  ("Kantar",                                "Research"),
    "kantar":                        ("Kantar",                                "Research"),
    "karma":                         ("Karma",                                 "Tech"),
    "klaviyo":                       ("Klaviyo × Qualtrics",                  "Tech"),
    "kommune":                       ("Kommune",                               "Agency"),
    "kpmg":                          ("KPMG",                                  "Consultancy"),
    "lefty":                         ("Lefty",                                 "Tech"),
    "lionelhitchen":                 ("Lionel Hitchen",                        "Industry"),
    "llyc":                          ("LLYC",                                  "Agency"),
    "m&g investment":                ("M&G Investments",                       "Financial"),
    "marian salzman":                ("Marian Salzman",                        "Research"),
    "marketscale":                   ("MarketScale",                           "Media"),
    "mccann":                        ("McCann",                                "Agency"),
    "mckinsey":                      ("McKinsey & Company",                    "Consultancy"),
    "mdlz":                          ("Mondelēz International",               "Industry"),
    "meltwater":                     ("Meltwater",                             "Tech"),
    "mercer":                        ("Mercer",                                "Consultancy"),
    "messari":                       ("Messari",                               "Research"),
    "meta":                          ("Meta",                                  "Tech"),
    "metricool":                     ("Metricool",                             "Tech"),
    "michael healy":                 ("Michael Healy-Rehn",                    "Research"),
    "microsoft":                     ("Microsoft",                             "Tech"),
    "momentum ww":                   ("Momentum Worldwide",                    "Agency"),
    "monotype":                      ("Monotype",                              "Tech"),
    "monte carlo":                   ("Monte Carlo Data",                      "Tech"),
    "natwest":                       ("NatWest",                               "Financial"),
    "newzoo":                        ("Newzoo",                                "Research"),
    "nextatlas":                     ("Nextatlas",                             "Research"),
    "nexxworks":                     ("Nexxworks",                             "Consultancy"),
    "nielsen":                       ("Nielsen",                               "Research"),
    "ofcom":                         ("Ofcom",                                 "Government"),
    "ogilvy":                        ("Ogilvy",                                "Agency"),
    "omg apac":                      ("Omnicom Media Group",                   "Agency"),
    "omg futures":                   ("Omnicom Media Group",                   "Agency"),
    "outlier":                       ("Outlier",                               "Research"),
    "pinterest":                     ("Pinterest",                             "Tech"),
    "pion":                          ("Pion",                                  "Research"),
    "plan a":                        ("Plan A",                                "Consultancy"),
    "positive luxury":               ("Positive Luxury",                       "Research"),
    "pr lab":                        ("PR Lab",                                "Agency"),
    "prophet":                       ("Prophet",                               "Consultancy"),
    "prowly":                        ("Prowly",                                "Tech"),
    "publicis":                      ("Publicis Commerce",                     "Agency"),
    "pwc":                           ("PwC",                                   "Consultancy"),
    "red antler":                    ("Red Antler",                            "Agency"),
    "refinitiv":                     ("Refinitiv (LSEG)",                      "Financial"),
    "resonate":                      ("Resonate",                              "Research"),
    "resy":                          ("Resy",                                  "Industry"),
    "reuters institute":             ("Reuters Institute",                     "Research"),
    "reuters-newman":                ("Reuters Institute",                     "Research"),
    "robeco":                        ("Robeco",                                "Financial"),
    "s&p":                           ("S&P Global",                            "Research"),
    "santander private":             ("Santander Private Banking",             "Financial"),
    "schroders":                     ("Schroders",                             "Financial"),
    "siemens":                       ("Siemens",                               "Tech"),
    "sked social":                   ("Sked Social",                           "Tech"),
    "smallworld":                    ("Small World",                           "Agency"),
    "snowflake":                     ("Snowflake",                             "Tech"),
    "softtech":                      ("SoftTech",                              "Tech"),
    "solve":                         ("Solve",                                 "Tech"),
    "spgmi":                         ("S&P Global Market Intelligence",        "Research"),
    "springwise":                    ("Springwise",                            "Research"),
    "stills":                        ("STILLS",                                "Agency"),
    "stitchfix":                     ("Stitch Fix",                            "Industry"),
    "stocksy":                       ("Stocksy",                               "Tech"),
    "stories_2071":                  ("Stories2071",                           "Research"),
    "strava":                        ("Strava",                                "Industry"),
    "syndio":                        ("Syndio",                                "Tech"),
    "talent alpha":                  ("Talent Alpha",                          "Tech"),
    "tbwa":                          ("TBWA",                                  "Agency"),
    "territory influence":           ("Territory Influence",                   "Agency"),
    "the block":                     ("The Block",                             "Research"),
    "the drawing arm":               ("The Drawing Arm",                       "Agency"),
    "the insights family":           ("The Insights Family",                   "Research"),
    "the media store":               ("The Media Store",                       "Agency"),
    "the new consumer":              ("The New Consumer × Coefficient Capital","Research"),
    "the realreal":                  ("The RealReal",                          "Industry"),
    "the wellhub":                   ("Wellhub",                               "Industry"),
    "tik tok":                       ("TikTok",                                "Tech"),
    "tiktok":                        ("TikTok",                                "Tech"),
    "tinder":                        ("Tinder",                                "Tech"),
    "torque":                        ("Torque",                                "Agency"),
    "totem":                         ("Totem",                                 "Agency"),
    "tracksuit":                     ("Tracksuit",                             "Tech"),
    "translink":                     ("Translink Corporate Finance",           "Financial"),
    "trendo":                        ("Trendo.mx",                             "Research"),
    "trendwatching":                 ("TrendWatching",                         "Research"),
    "triple a":                      ("Triple-A",                              "Research"),
    "ubs":                           ("UBS",                                   "Financial"),
    "udemy":                         ("Udemy",                                 "Tech"),
    "ultra violet":                  ("Ultra Violet",                          "Research"),
    "un global pulse":               ("UN Global Pulse",                       "UN & IGO"),
    "undp":                          ("UNDP",                                  "UN & IGO"),
    "unicef":                        ("UNICEF",                                "UN & IGO"),
    "upstack":                       ("Upstack",                               "Tech"),
    "vice":                          ("VICE",                                  "Media"),
    "vml the cocktail":              ("VML × The Cocktail",                   "Agency"),
    "vml":                           ("VML",                                   "Agency"),
    "warc":                          ("WARC × TikTok",                        "Research"),
    "weber forecast":                ("Weber Forecast",                        "Research"),
    "wef":                           ("World Economic Forum",                  "Research"),
    "world economic forum":          ("World Economic Forum",                  "Research"),
    "wgsn":                          ("WGSN",                                  "Research"),
    "world food programme":          ("World Food Programme",                  "UN & IGO"),
    "yondr":                         ("YONDR",                                 "Agency"),
    "youpix":                        ("YOUPIX",                                "Research"),
    "youtube":                       ("YouTube",                               "Tech"),
    "zendesk":                       ("Zendesk",                               "Tech"),
}


def lookup_org(filename: str) -> tuple[str, str]:
    """Return (org, orgType) for a given report filename."""
    key = filename.lower().replace("_", " ").replace("-", " ").replace(".pdf", "")
    # Try longest match first
    best = None
    best_len = 0
    for prefix, val in ORG_MAP.items():
        if key.startswith(prefix) and len(prefix) > best_len:
            best = val
            best_len = len(prefix)
    if best:
        return best
    # Fallback: try any substring match
    for prefix, val in ORG_MAP.items():
        if prefix in key:
            return val
    return ("Unknown", "Research")


def main():
    result_files = sorted(BATCHES_DIR.glob("result_*.json"))
    tagged = 0
    unknown = []

    for path in result_files:
        with open(path) as f:
            data = json.load(f)

        for entry in data.get("entries", []):
            org, org_type = lookup_org(entry["filename"])
            entry["org"]     = org
            entry["orgType"] = org_type
            tagged += 1
            if org == "Unknown":
                unknown.append(entry["filename"])

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    print(f"✓ Tagged {tagged} entries across {len(result_files)} batch files.")
    if unknown:
        print(f"\n⚠  Could not identify org for {len(unknown)} entries:")
        for fn in unknown:
            print(f"   {fn}")
    else:
        print("  All entries matched successfully.")


if __name__ == "__main__":
    main()
