#!/usr/bin/env python3
"""
Foresight Cosmos — Macro-planet consolidator.
Collapses 427 granular trends into 19 macro-planet themes.
Spatial ordering baked into array sequence for Fibonacci proximity clustering.

Usage:
  python macro_consolidate.py
"""

import json
from pathlib import Path
from datetime import datetime

COSMOS_IN  = Path("../data/cosmos.json")
COSMOS_OUT = Path("../data/cosmos.json")

# ── Spatial order (consecutive = closer on Fibonacci sphere) ──────────────────
# Desired proximity chains:
#   AI Infra ↔ Cybersecurity
#   AI Creativity → Creator Economy → Brand → Consumer → Fashion
ORDERED_PLANETS = [
    "AI: Infrastructure, Capability & Governance",
    "Cybersecurity & Data",
    "AI in Business & Work",
    "AI in Creativity & Culture",
    "Creator Economy & Social Media",
    "Brand, Marketing & Advertising",
    "Consumer Behavior & Identity",
    "Fashion, Luxury & Aesthetics",
    "Health & Medicine",
    "Wellbeing & Mental Health",
    "Future of Work",
    "Climate & Sustainability",
    "Geopolitics & Economic Order",
    "Financial Markets & Investment",
    "Emerging Tech, Crypto & Web3",
    "Food & Nutrition",
    "Travel & Experience",
    "Gaming, Entertainment & Media",
    "Futures & Foresight",
]

PLANET_DESCRIPTIONS = {
    "AI: Infrastructure, Capability & Governance": "The foundational layer of the AI era — from compute scarcity and model architecture to regulatory frameworks and governance deficits. Covers the infrastructure, capability race, and institutional responses that determine how AI develops and who controls it.",
    "Cybersecurity & Data": "Security as the unavoidable foundation of all technology strategy — encompassing data governance, privacy architecture, quantum-cryptography convergence, and the collective resilience challenge of protecting critical digital infrastructure.",
    "AI in Business & Work": "AI transforming how organizations operate, compete, and deliver value — from enterprise deployment and knowledge work automation to talent gaps, legal transformation, and the shift from AI experimentation to measurable business returns.",
    "AI in Creativity & Culture": "AI reshaping the creative economy — from brand homogenization and algorithmic aesthetics to the human creativity premium, empathetic AI design, and the cultural question of what it means to make something in an era of generative abundance.",
    "Creator Economy & Social Media": "The shift from broadcast to participatory culture — as creators become the primary cultural force, fans become creators, and social platforms displace traditional media as the infrastructure of influence, commerce, and information.",
    "Brand, Marketing & Advertising": "The transformation of brand strategy, media buying, and marketing effectiveness — from retail media surpassing big tech to the death of cookies, the rise of cultural relevance as the primary brand asset, and AI rewriting advertising workflows.",
    "Consumer Behavior & Identity": "The deep shifts in how people consume, identify, and make meaning — from cost-of-living behavioral persistence and micro-happiness coping to generational divergence, the retreat to private life, and identity as a contested site of cultural and commercial value.",
    "Fashion, Luxury & Aesthetics": "The aesthetics, identity politics, and economics of fashion and luxury — from the grassroots democratization of trend-setting and the resale investment thesis to craft revival, analog aesthetics, and design as a response to AI-era uncertainty.",
    "Health & Medicine": "The transformation of health and medicine through AI, genomics, and personalization — from AI-enabled drug discovery and FemTech to GLP-1's market disruption, the hyperconnected patient, and the decentralization of health infrastructure.",
    "Wellbeing & Mental Health": "The evolution of wellbeing as a primary cultural and commercial value — from biohacking and strength training's dominance to social fitness, engineered connection, and the backlash against technology's erosion of quality of life.",
    "Future of Work": "The structural transformation of work — from hybrid permanence and boundary-setting to skills-based hiring, pay equity mandates, AI's impact on knowledge roles, and the organizational redesign required to sustain human performance amid technological acceleration.",
    "Climate & Sustainability": "Climate as a strategic forcing function across investment, innovation, and consumption — from the 2030 deadline as a genuine catalyst to the EV transition's slower-than-expected pace, the great sustainability bifurcation, and circular economy normalization.",
    "Geopolitics & Economic Order": "The fracturing and recomposition of the global order — from multipolarity and strategic reshoring to polycrisis as a permanent operating context, the rise of geopolitical swing states, and fiscal spending as a structural force reshaping growth.",
    "Financial Markets & Investment": "The financial landscape navigating higher-for-longer rates, political repricing, and structural transformation — from private markets' vulnerabilities and M&A evolution to crypto institutionalization, blended finance for impact, and the end of the Goldilocks era.",
    "Emerging Tech, Crypto & Web3": "The convergence of next-generation technologies — spatial computing, quantum, blockchain, crypto, and industrial IoT — into a new technological substrate that is reshaping industry, value exchange, and physical-digital integration.",
    "Food & Nutrition": "The transformation of food as a civilizational system — from AI-driven flavor development and snackification to food insecurity at humanitarian scale, the functional food boom, and consumer navigation of health and indulgence simultaneously.",
    "Travel & Experience": "The evolution of travel and experience as primary consumer priorities — from taste-led and collective travel to vacation maximization, the spectacle economy's return, and restaurants and live events as essential third-place infrastructure.",
    "Gaming, Entertainment & Media": "The convergence of gaming, entertainment, and media into a unified culture and commerce platform — from transmedia franchises and AI-generated worlds to journalism's existential crisis, fandom as cultural production, and gaming logic entering real-world engagement.",
    "Futures & Foresight": "The emerging discipline of anticipatory thinking as a governance and strategic capability — from megatrend navigation and radical uncertainty as a strategic condition to youth foresight as a rights-based practice and ontological shocks disrupting how futures are imagined.",
}

# ── Complete mapping: old trend ID → macro-planet name ───────────────────────
TREND_TO_PLANET = {
    "t001": "Financial Markets & Investment",
    "t002": "AI in Business & Work",
    "t003": "Emerging Tech, Crypto & Web3",
    "t004": "Climate & Sustainability",
    "t005": "AI in Business & Work",
    "t006": "AI: Infrastructure, Capability & Governance",
    "t007": "AI in Business & Work",
    "t008": "AI: Infrastructure, Capability & Governance",
    "t009": "AI: Infrastructure, Capability & Governance",
    "t010": "AI: Infrastructure, Capability & Governance",
    "t011": "Emerging Tech, Crypto & Web3",
    "t012": "Brand, Marketing & Advertising",
    "t013": "Brand, Marketing & Advertising",
    "t014": "Food & Nutrition",
    "t015": "Brand, Marketing & Advertising",
    "t016": "Brand, Marketing & Advertising",
    "t017": "AI in Creativity & Culture",
    "t018": "Cybersecurity & Data",
    "t019": "Financial Markets & Investment",
    "t020": "Geopolitics & Economic Order",
    "t021": "Gaming, Entertainment & Media",
    "t022": "Brand, Marketing & Advertising",
    "t023": "Geopolitics & Economic Order",
    "t024": "Geopolitics & Economic Order",
    "t025": "Financial Markets & Investment",
    "t026": "Financial Markets & Investment",
    "t027": "Travel & Experience",
    "t028": "Geopolitics & Economic Order",
    "t029": "Geopolitics & Economic Order",
    "t030": "Climate & Sustainability",
    "t031": "Emerging Tech, Crypto & Web3",
    "t032": "Health & Medicine",
    "t033": "Emerging Tech, Crypto & Web3",
    "t034": "Health & Medicine",
    "t035": "AI in Creativity & Culture",
    "t036": "Creator Economy & Social Media",
    "t037": "Fashion, Luxury & Aesthetics",
    "t038": "Health & Medicine",
    "t039": "Health & Medicine",
    "t040": "Health & Medicine",
    "t041": "Emerging Tech, Crypto & Web3",
    "t042": "Wellbeing & Mental Health",
    "t043": "Futures & Foresight",
    "t044": "Futures & Foresight",
    "t045": "Gaming, Entertainment & Media",
    "t046": "Consumer Behavior & Identity",
    "t047": "Climate & Sustainability",
    "t048": "Financial Markets & Investment",
    "t049": "Creator Economy & Social Media",
    "t050": "Brand, Marketing & Advertising",
    "t051": "Financial Markets & Investment",
    "t052": "Climate & Sustainability",
    "t053": "Brand, Marketing & Advertising",
    "t054": "Brand, Marketing & Advertising",
    "t055": "Consumer Behavior & Identity",
    "t056": "Wellbeing & Mental Health",
    "t057": "Emerging Tech, Crypto & Web3",
    "t058": "Emerging Tech, Crypto & Web3",
    "t059": "Geopolitics & Economic Order",
    "t060": "Health & Medicine",
    "t061": "Food & Nutrition",
    "t062": "Fashion, Luxury & Aesthetics",
    "t063": "Food & Nutrition",
    "t064": "Creator Economy & Social Media",
    "t065": "Creator Economy & Social Media",
    "t066": "Travel & Experience",
    "t067": "Travel & Experience",
    "t068": "Climate & Sustainability",
    "t069": "Consumer Behavior & Identity",
    "t070": "AI: Infrastructure, Capability & Governance",
    "t071": "Cybersecurity & Data",
    "t072": "Climate & Sustainability",
    "t073": "Fashion, Luxury & Aesthetics",
    "t074": "AI: Infrastructure, Capability & Governance",
    "t075": "AI in Business & Work",
    "t076": "Emerging Tech, Crypto & Web3",
    "t077": "Consumer Behavior & Identity",
    "t078": "Geopolitics & Economic Order",
    "t079": "Emerging Tech, Crypto & Web3",
    "t080": "Emerging Tech, Crypto & Web3",
    "t081": "Emerging Tech, Crypto & Web3",
    "t082": "Brand, Marketing & Advertising",
    "t083": "Brand, Marketing & Advertising",
    "t084": "AI in Creativity & Culture",
    "t085": "Brand, Marketing & Advertising",
    "t086": "AI in Business & Work",
    "t087": "Financial Markets & Investment",
    "t088": "Creator Economy & Social Media",
    "t089": "Creator Economy & Social Media",
    "t090": "Creator Economy & Social Media",
    "t091": "AI in Business & Work",
    "t092": "AI: Infrastructure, Capability & Governance",
    "t093": "Brand, Marketing & Advertising",
    "t094": "Consumer Behavior & Identity",
    "t095": "AI: Infrastructure, Capability & Governance",
    "t096": "AI: Infrastructure, Capability & Governance",
    "t097": "Emerging Tech, Crypto & Web3",
    "t098": "Cybersecurity & Data",
    "t099": "Emerging Tech, Crypto & Web3",
    "t100": "Future of Work",
    "t101": "Wellbeing & Mental Health",
    "t102": "Climate & Sustainability",
    "t103": "Emerging Tech, Crypto & Web3",
    "t104": "Financial Markets & Investment",
    "t105": "Health & Medicine",
    "t106": "Health & Medicine",
    "t107": "Health & Medicine",
    "t108": "AI in Creativity & Culture",
    "t109": "Wellbeing & Mental Health",
    "t110": "Consumer Behavior & Identity",
    "t111": "Brand, Marketing & Advertising",
    "t112": "Futures & Foresight",
    "t113": "AI: Infrastructure, Capability & Governance",
    "t114": "Consumer Behavior & Identity",
    "t115": "Wellbeing & Mental Health",
    "t116": "Emerging Tech, Crypto & Web3",
    "t117": "Wellbeing & Mental Health",
    "t118": "Brand, Marketing & Advertising",
    "t119": "Brand, Marketing & Advertising",
    "t120": "Creator Economy & Social Media",
    "t121": "Creator Economy & Social Media",
    "t122": "Brand, Marketing & Advertising",
    "t123": "Financial Markets & Investment",
    "t124": "Consumer Behavior & Identity",
    "t125": "Consumer Behavior & Identity",
    "t126": "Futures & Foresight",
    "t127": "Consumer Behavior & Identity",
    "t128": "Geopolitics & Economic Order",
    "t129": "Consumer Behavior & Identity",
    "t130": "Food & Nutrition",
    "t131": "Brand, Marketing & Advertising",
    "t132": "Cybersecurity & Data",
    "t133": "Climate & Sustainability",
    "t134": "Climate & Sustainability",
    "t135": "Geopolitics & Economic Order",
    "t136": "Emerging Tech, Crypto & Web3",
    "t137": "Emerging Tech, Crypto & Web3",
    "t138": "Future of Work",
    "t139": "Geopolitics & Economic Order",
    "t140": "Geopolitics & Economic Order",
    "t141": "Gaming, Entertainment & Media",
    "t142": "AI in Creativity & Culture",
    "t143": "Futures & Foresight",
    "t144": "Financial Markets & Investment",
    "t145": "Brand, Marketing & Advertising",
    "t146": "AI: Infrastructure, Capability & Governance",
    "t147": "Cybersecurity & Data",
    "t148": "AI: Infrastructure, Capability & Governance",
    "t149": "Futures & Foresight",
    "t150": "Emerging Tech, Crypto & Web3",
    "t151": "Health & Medicine",
    "t152": "AI in Business & Work",
    "t153": "Brand, Marketing & Advertising",
    "t154": "Fashion, Luxury & Aesthetics",
    "t155": "AI in Creativity & Culture",
    "t156": "Fashion, Luxury & Aesthetics",
    "t157": "Emerging Tech, Crypto & Web3",
    "t158": "AI in Business & Work",
    "t159": "Emerging Tech, Crypto & Web3",
    "t160": "Financial Markets & Investment",
    "t161": "Financial Markets & Investment",
    "t162": "Financial Markets & Investment",
    "t163": "AI: Infrastructure, Capability & Governance",
    "t164": "AI: Infrastructure, Capability & Governance",
    "t165": "AI: Infrastructure, Capability & Governance",
    "t166": "Emerging Tech, Crypto & Web3",
    "t167": "Cybersecurity & Data",
    "t168": "AI in Creativity & Culture",
    "t169": "Brand, Marketing & Advertising",
    "t170": "Consumer Behavior & Identity",
    "t171": "Consumer Behavior & Identity",
    "t172": "AI: Infrastructure, Capability & Governance",
    "t173": "Geopolitics & Economic Order",
    "t174": "Fashion, Luxury & Aesthetics",
    "t175": "Consumer Behavior & Identity",
    "t176": "Travel & Experience",
    "t177": "Travel & Experience",
    "t178": "Gaming, Entertainment & Media",
    "t179": "Brand, Marketing & Advertising",
    "t180": "Futures & Foresight",
    "t181": "Wellbeing & Mental Health",
    "t182": "Consumer Behavior & Identity",
    "t183": "Brand, Marketing & Advertising",
    "t184": "AI in Business & Work",
    "t185": "Financial Markets & Investment",
    "t186": "Creator Economy & Social Media",
    "t187": "Creator Economy & Social Media",
    "t188": "AI in Business & Work",
    "t189": "AI in Business & Work",
    "t190": "Climate & Sustainability",
    "t191": "Geopolitics & Economic Order",
    "t192": "Consumer Behavior & Identity",
    "t193": "Wellbeing & Mental Health",
    "t194": "Travel & Experience",
    "t195": "AI in Business & Work",
    "t196": "Consumer Behavior & Identity",
    "t197": "AI in Business & Work",
    "t198": "Emerging Tech, Crypto & Web3",
    "t199": "Emerging Tech, Crypto & Web3",
    "t200": "Financial Markets & Investment",
    "t201": "Financial Markets & Investment",
    "t202": "Health & Medicine",
    "t203": "Health & Medicine",
    "t204": "Brand, Marketing & Advertising",
    "t205": "Brand, Marketing & Advertising",
    "t206": "AI in Business & Work",
    "t207": "AI: Infrastructure, Capability & Governance",
    "t208": "Climate & Sustainability",
    "t209": "Future of Work",
    "t210": "Creator Economy & Social Media",
    "t211": "Geopolitics & Economic Order",
    "t212": "Financial Markets & Investment",
    "t213": "Geopolitics & Economic Order",
    "t214": "Consumer Behavior & Identity",
    "t215": "Consumer Behavior & Identity",
    "t216": "AI: Infrastructure, Capability & Governance",
    "t217": "AI: Infrastructure, Capability & Governance",
    "t218": "Financial Markets & Investment",
    "t219": "Financial Markets & Investment",
    "t220": "AI: Infrastructure, Capability & Governance",
    "t221": "Health & Medicine",
    "t222": "Climate & Sustainability",
    "t223": "Brand, Marketing & Advertising",
    "t224": "Consumer Behavior & Identity",
    "t225": "Consumer Behavior & Identity",
    "t226": "Consumer Behavior & Identity",
    "t227": "Consumer Behavior & Identity",
    "t228": "Geopolitics & Economic Order",
    "t229": "Geopolitics & Economic Order",
    "t230": "Creator Economy & Social Media",
    "t231": "AI in Creativity & Culture",
    "t232": "Emerging Tech, Crypto & Web3",
    "t233": "Emerging Tech, Crypto & Web3",
    "t234": "Financial Markets & Investment",
    "t235": "Financial Markets & Investment",
    "t236": "Financial Markets & Investment",
    "t237": "Geopolitics & Economic Order",
    "t238": "Gaming, Entertainment & Media",
    "t239": "Gaming, Entertainment & Media",
    "t240": "Brand, Marketing & Advertising",
    "t241": "Creator Economy & Social Media",
    "t242": "Brand, Marketing & Advertising",
    "t243": "Consumer Behavior & Identity",
    "t244": "Future of Work",
    "t245": "Consumer Behavior & Identity",
    "t246": "Consumer Behavior & Identity",
    "t247": "Health & Medicine",
    "t248": "Futures & Foresight",
    "t249": "Futures & Foresight",
    "t250": "AI: Infrastructure, Capability & Governance",
    "t251": "AI in Business & Work",
    "t252": "Fashion, Luxury & Aesthetics",
    "t253": "Food & Nutrition",
    "t254": "Food & Nutrition",
    "t255": "Health & Medicine",
    "t256": "Health & Medicine",
    "t257": "Financial Markets & Investment",
    "t258": "Geopolitics & Economic Order",
    "t259": "Consumer Behavior & Identity",
    "t260": "Future of Work",
    "t261": "Wellbeing & Mental Health",
    "t262": "AI in Creativity & Culture",
    "t263": "Consumer Behavior & Identity",
    "t264": "AI in Business & Work",
    "t265": "Creator Economy & Social Media",
    "t266": "Consumer Behavior & Identity",
    "t267": "Brand, Marketing & Advertising",
    "t268": "Wellbeing & Mental Health",
    "t269": "Food & Nutrition",
    "t270": "Food & Nutrition",
    "t271": "Food & Nutrition",
    "t272": "Food & Nutrition",
    "t273": "AI in Business & Work",
    "t274": "Financial Markets & Investment",
    "t275": "Emerging Tech, Crypto & Web3",
    "t276": "Emerging Tech, Crypto & Web3",
    "t277": "Creator Economy & Social Media",
    "t278": "Futures & Foresight",
    "t279": "AI in Business & Work",
    "t280": "Future of Work",
    "t281": "Consumer Behavior & Identity",
    "t282": "Wellbeing & Mental Health",
    "t283": "Fashion, Luxury & Aesthetics",
    "t284": "Fashion, Luxury & Aesthetics",
    "t285": "AI: Infrastructure, Capability & Governance",
    "t286": "Cybersecurity & Data",
    "t287": "Geopolitics & Economic Order",
    "t288": "Gaming, Entertainment & Media",
    "t289": "Gaming, Entertainment & Media",
    "t290": "Health & Medicine",
    "t291": "Health & Medicine",
    "t292": "Fashion, Luxury & Aesthetics",
    "t293": "Fashion, Luxury & Aesthetics",
    "t294": "Futures & Foresight",
    "t295": "Brand, Marketing & Advertising",
    "t296": "Brand, Marketing & Advertising",
    "t297": "Creator Economy & Social Media",
    "t298": "Brand, Marketing & Advertising",
    "t299": "Brand, Marketing & Advertising",
    "t300": "Creator Economy & Social Media",
    "t301": "Consumer Behavior & Identity",
    "t302": "Travel & Experience",
    "t303": "Cybersecurity & Data",
    "t304": "Gaming, Entertainment & Media",
    "t305": "Climate & Sustainability",
    "t306": "Emerging Tech, Crypto & Web3",
    "t307": "Fashion, Luxury & Aesthetics",
    "t308": "Fashion, Luxury & Aesthetics",
    "t309": "AI in Creativity & Culture",
    "t310": "Consumer Behavior & Identity",
    "t311": "Climate & Sustainability",
    "t312": "Climate & Sustainability",
    "t313": "AI: Infrastructure, Capability & Governance",
    "t314": "Fashion, Luxury & Aesthetics",
    "t315": "Fashion, Luxury & Aesthetics",
    "t316": "Brand, Marketing & Advertising",
    "t317": "Brand, Marketing & Advertising",
    "t318": "Brand, Marketing & Advertising",
    "t319": "Brand, Marketing & Advertising",
    "t320": "Brand, Marketing & Advertising",
    "t321": "AI in Business & Work",
    "t322": "Brand, Marketing & Advertising",
    "t323": "Financial Markets & Investment",
    "t324": "Future of Work",
    "t325": "Cybersecurity & Data",
    "t326": "Cybersecurity & Data",
    "t327": "Emerging Tech, Crypto & Web3",
    "t328": "Brand, Marketing & Advertising",
    "t329": "Brand, Marketing & Advertising",
    "t330": "Financial Markets & Investment",
    "t331": "Consumer Behavior & Identity",
    "t332": "Travel & Experience",
    "t333": "Gaming, Entertainment & Media",
    "t334": "Creator Economy & Social Media",
    "t335": "Gaming, Entertainment & Media",
    "t336": "Gaming, Entertainment & Media",
    "t337": "Financial Markets & Investment",
    "t338": "AI in Business & Work",
    "t339": "AI in Business & Work",
    "t340": "Geopolitics & Economic Order",
    "t341": "Financial Markets & Investment",
    "t342": "Geopolitics & Economic Order",
    "t343": "Financial Markets & Investment",
    "t344": "Emerging Tech, Crypto & Web3",
    "t345": "Brand, Marketing & Advertising",
    "t346": "AI: Infrastructure, Capability & Governance",
    "t347": "AI: Infrastructure, Capability & Governance",
    "t348": "Wellbeing & Mental Health",
    "t349": "Future of Work",
    "t350": "AI in Business & Work",
    "t351": "AI: Infrastructure, Capability & Governance",
    "t352": "AI: Infrastructure, Capability & Governance",
    "t353": "Climate & Sustainability",
    "t354": "Fashion, Luxury & Aesthetics",
    "t355": "Fashion, Luxury & Aesthetics",
    "t356": "Fashion, Luxury & Aesthetics",
    "t357": "Wellbeing & Mental Health",
    "t358": "Wellbeing & Mental Health",
    "t359": "Wellbeing & Mental Health",
    "t360": "Future of Work",
    "t361": "Future of Work",
    "t362": "AI: Infrastructure, Capability & Governance",
    "t363": "Consumer Behavior & Identity",
    "t364": "Climate & Sustainability",
    "t365": "Creator Economy & Social Media",
    "t366": "Creator Economy & Social Media",
    "t367": "Emerging Tech, Crypto & Web3",
    "t368": "Brand, Marketing & Advertising",
    "t369": "Consumer Behavior & Identity",
    "t370": "Gaming, Entertainment & Media",
    "t371": "Consumer Behavior & Identity",
    "t372": "Consumer Behavior & Identity",
    "t373": "Consumer Behavior & Identity",
    "t374": "Food & Nutrition",
    "t375": "Fashion, Luxury & Aesthetics",
    "t376": "Fashion, Luxury & Aesthetics",
    "t377": "Wellbeing & Mental Health",
    "t378": "Wellbeing & Mental Health",
    "t379": "Creator Economy & Social Media",
    "t380": "Creator Economy & Social Media",
    "t381": "Creator Economy & Social Media",
    "t382": "Creator Economy & Social Media",
    "t383": "Consumer Behavior & Identity",
    "t384": "Future of Work",
    "t385": "Future of Work",
    "t386": "Consumer Behavior & Identity",
    "t387": "Brand, Marketing & Advertising",
    "t388": "Financial Markets & Investment",
    "t389": "AI: Infrastructure, Capability & Governance",
    "t390": "Climate & Sustainability",
    "t391": "Travel & Experience",
    "t392": "Consumer Behavior & Identity",
    "t393": "Brand, Marketing & Advertising",
    "t394": "Consumer Behavior & Identity",
    "t395": "Financial Markets & Investment",
    "t396": "Financial Markets & Investment",
    "t397": "AI: Infrastructure, Capability & Governance",
    "t398": "Future of Work",
    "t399": "Future of Work",
    "t400": "Health & Medicine",
    "t401": "Health & Medicine",
    "t402": "Futures & Foresight",
    "t403": "Futures & Foresight",
    "t404": "Futures & Foresight",
    "t405": "Cybersecurity & Data",
    "t406": "AI in Business & Work",
    "t407": "Fashion, Luxury & Aesthetics",
    "t408": "AI in Creativity & Culture",
    "t409": "AI in Creativity & Culture",
    "t410": "Fashion, Luxury & Aesthetics",
    "t411": "AI in Creativity & Culture",
    "t412": "Climate & Sustainability",
    "t413": "Brand, Marketing & Advertising",
    "t414": "Consumer Behavior & Identity",
    "t415": "Consumer Behavior & Identity",
    "t416": "Climate & Sustainability",
    "t417": "AI: Infrastructure, Capability & Governance",
    "t418": "Cybersecurity & Data",
    "t419": "Future of Work",
    "t420": "Consumer Behavior & Identity",
    "t421": "Emerging Tech, Crypto & Web3",
    "t422": "Food & Nutrition",
    "t423": "Brand, Marketing & Advertising",
    "t424": "Creator Economy & Social Media",
    "t425": "Creator Economy & Social Media",
    "t426": "Gaming, Entertainment & Media",
    "t427": "AI in Business & Work",
}


def build_macro_cosmos(cosmos):
    old_trends   = {t["id"]: t for t in cosmos["trends"]}
    old_signals  = cosmos["signals"]
    old_scenarios = cosmos["scenarios"]

    # ── Build macro-planet buckets ──
    planet_buckets = {name: {"trend_ids": [], "signal_ids": [], "scenario_ids": [],
                              "sources": [], "years": []}
                      for name in ORDERED_PLANETS}

    # Map old trend IDs into planet buckets
    for old_id, planet_name in TREND_TO_PLANET.items():
        if old_id not in old_trends:
            continue
        old_t = old_trends[old_id]
        bucket = planet_buckets[planet_name]
        bucket["trend_ids"].append(old_id)
        bucket["sources"].extend(old_t.get("sources", []))
        bucket["years"].extend(
            s["year"] for s in old_t.get("sources", []) if s.get("year")
        )

    # Map signals → planet via their connections
    sig_to_planet = {}
    for sig in old_signals:
        # Use the first valid connection to determine planet
        for conn in sig.get("connections", []):
            planet_name = TREND_TO_PLANET.get(conn)
            if planet_name:
                sig_to_planet[sig["id"]] = planet_name
                planet_buckets[planet_name]["signal_ids"].append(sig["id"])
                planet_buckets[planet_name]["years"].extend(
                    s["year"] for s in sig.get("sources", []) if s.get("year")
                )
                break
        else:
            # No valid connection found — assign to first listed planet as fallback
            planet_buckets[ORDERED_PLANETS[0]]["signal_ids"].append(sig["id"])

    # Map scenarios → planet via their parent trend
    for sc in old_scenarios:
        parent_trend = sc.get("trend", "")
        planet_name  = TREND_TO_PLANET.get(parent_trend, ORDERED_PLANETS[0])
        planet_buckets[planet_name]["scenario_ids"].append(sc["id"])

    # ── Build new macro trend objects ──
    new_trends = []
    planet_name_to_id = {}
    for i, name in enumerate(ORDERED_PLANETS):
        pid = f"t{i+1:03d}"
        planet_name_to_id[name] = pid
        bucket = planet_buckets[name]
        years  = bucket["years"]
        new_trends.append({
            "id":          pid,
            "name":        name,
            "description": PLANET_DESCRIPTIONS[name],
            "sources":     bucket["sources"],
            "signals":     [],   # filled in after signal rebuild
            "scenarios":   [],   # filled in after scenario rebuild
            "firstSeen":   min(years) if years else 2024,
            "lastSeen":    max(years) if years else 2025,
            "mass":        1.0,  # recalculated below
        })

    trend_id_map = {t["id"]: t for t in new_trends}

    # ── Rebuild signals with new planet connections ──
    new_signals = []
    for i, sig in enumerate(old_signals):
        new_planet_name = sig_to_planet.get(sig["id"])
        if not new_planet_name:
            new_planet_name = ORDERED_PLANETS[0]
        new_pid = planet_name_to_id[new_planet_name]

        # Extend connections to adjacent planets for richer graph (up to 2 planets)
        connections = [new_pid]
        planet_idx = ORDERED_PLANETS.index(new_planet_name)
        # Add nearest neighbour if signal also connected to a trend from adjacent planet
        old_connections = sig.get("connections", [])
        for conn in old_connections[1:]:
            alt_planet = TREND_TO_PLANET.get(conn)
            if alt_planet and alt_planet != new_planet_name:
                alt_pid = planet_name_to_id[alt_planet]
                if alt_pid not in connections:
                    connections.append(alt_pid)
                    break

        new_sig = {
            "id":          f"s{i+1:03d}",
            "name":        sig["name"],
            "description": sig["description"],
            "sources":     sig.get("sources", []),
            "firstSeen":   sig.get("firstSeen", 2024),
            "lastSeen":    sig.get("lastSeen", 2024),
            "strength":    sig.get("strength", 0.6),
            "connections": connections,
        }
        new_signals.append(new_sig)
        # Register with parent planet
        for pid in connections:
            if pid in trend_id_map and new_sig["id"] not in trend_id_map[pid]["signals"]:
                trend_id_map[pid]["signals"].append(new_sig["id"])

    # ── Rebuild scenarios ──
    new_scenarios = []
    for i, sc in enumerate(old_scenarios):
        parent_planet = TREND_TO_PLANET.get(sc.get("trend", ""), ORDERED_PLANETS[0])
        new_pid = planet_name_to_id[parent_planet]
        new_sc = {
            "id":          f"sc{i+1:03d}",
            "name":        sc["name"],
            "description": sc["description"],
            "trend":       new_pid,
            "sources":     sc.get("sources", []),
        }
        new_scenarios.append(new_sc)
        if new_sc["id"] not in trend_id_map[new_pid]["scenarios"]:
            trend_id_map[new_pid]["scenarios"].append(new_sc["id"])

    # ── Recalculate mass ──
    for t in new_trends:
        sig_count = len(t["signals"])
        sc_count  = len(t["scenarios"])
        t["mass"] = round(min(2.5, 1.0 + sig_count * 0.04 + sc_count * 0.15), 2)

    return new_trends, new_signals, new_scenarios


def main():
    print("Reading cosmos.json...")
    with open(COSMOS_IN) as f:
        cosmos = json.load(f)

    print(f"  Input: {len(cosmos['trends'])} trends, {len(cosmos['signals'])} signals, {len(cosmos['scenarios'])} scenarios")

    # Check for unmapped trend IDs
    all_old_ids = {t["id"] for t in cosmos["trends"]}
    mapped_ids  = set(TREND_TO_PLANET.keys())
    unmapped    = all_old_ids - mapped_ids
    if unmapped:
        print(f"  WARNING: {len(unmapped)} unmapped trend IDs (will fall back to planet 1): {sorted(unmapped)[:10]}")

    print("Building macro-planet cosmos...")
    new_trends, new_signals, new_scenarios = build_macro_cosmos(cosmos)

    all_years = [s["year"] for sig in new_signals for s in sig.get("sources", []) if s.get("year")]

    output = {
        "meta": {
            "generated":   datetime.now().isoformat()[:10],
            "reportCount": cosmos["meta"].get("reportCount", 274),
            "yearRange":   [min(all_years, default=2023), max(all_years, default=2025)],
        },
        "signals":   new_signals,
        "trends":    new_trends,
        "scenarios": new_scenarios,
    }

    with open(COSMOS_OUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Written to {COSMOS_OUT}")
    print(f"  {len(new_trends)} macro-planets · {len(new_signals)} signals · {len(new_scenarios)} scenarios")
    print("\nPlanet signal counts:")
    for t in new_trends:
        print(f"  {t['name'][:50]:<50}  {len(t['signals']):>3} signals  mass={t['mass']}")


if __name__ == "__main__":
    main()
