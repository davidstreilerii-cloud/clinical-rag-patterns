"""
Domain routing: pick the collection a query belongs to.

A single flat index over mixed clinical content answers coverage questions out of
coding documents. Splitting the corpus by domain and routing to one collection is
the cheapest fix, and it does most of the work that fancier retrieval gets credit
for.

The routing table below is deliberately small and readable. A production system
carries a much larger vocabulary and a cross-collection fusion step for queries
that straddle domains; this is the shape of it, not the size of it.

**The fallback is the interesting part.** `route()` returns "general" when nothing
matches, rather than the highest-scoring domain. A router that always picks a
winner will happily answer a coverage question from the coding corpus and sound
confident doing it. "I do not know which domain this is" is information; discard
it and you cannot tell a routed answer from a guessed one.
"""
from __future__ import annotations

#: Collections in this example. `general` is where unrecognised queries go — it is
#: a real collection, not a sentinel, so an unrouted query still returns something
#: traceable rather than silently landing in whichever domain scored highest.
DOMAINS: tuple[str, ...] = ("coding", "coverage", "quality", "general")

#: Domain vocabulary. Terms are lowercase; matching is substring-based on a
#: lowercased query, which is enough for a readable example and is not what a
#: production router should do (see module docstring).
DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    # Classification and payment grouping: MS-DRG, HCC risk adjustment.
    "coding": (
        "drg", "ms-drg", "hcc", "risk adjustment", "risk-adjustment",
        "coefficient", "raf", "discharge", "discharges", "grouper",
        "icd", "severity", "cc/mcc", "case mix", "case-mix",
    ),
    # What Medicare will and will not pay for: NCDs and LCDs.
    "coverage": (
        "ncd", "lcd", "coverage", "covered", "cover", "medical necessity",
        "national coverage determination", "local coverage determination",
        "contractor", "indication", "criteria", "eligible",
    ),
    # Outcome and process measurement: readmissions, infections, mortality.
    "quality": (
        "readmission", "readmissions", "mortality", "complication",
        "complications", "infection", "sir", "clabsi", "cauti", "mrsa",
        "sepsis", "measure", "timely", "star rating", "penalty",
    ),
}

FALLBACK = "general"


def route(query: str) -> str:
    """
    Return the collection name for `query`, or FALLBACK if nothing matches.

    Scoring is a term count, and ties go to the first domain in DOMAIN_TERMS —
    deterministic, which matters more here than being clever. A real system would
    resolve ties by fusing across the tied collections rather than picking one.
    """
    lowered = query.lower()
    best, best_score = FALLBACK, 0
    for collection, terms in DOMAIN_TERMS.items():
        score = sum(1 for term in terms if term in lowered)
        if score > best_score:
            best, best_score = collection, score
    return best
