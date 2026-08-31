"""
Idempotent ingestion with entity tagging and mandatory provenance.

Three things happen here, in order of how much trouble their absence causes.

**Provenance is required, not optional.** Every file in `corpus/` carries a
four-field header — Source, Retrieved, Published, Subset — and `parse_provenance`
raises if it is missing. A document with no provenance is a document nobody can
cite, and once it is in the index it is indistinguishable from one that can be.
The private system this pattern comes from spent a week removing invented data
that had entered exactly that way: plausible content, no source, no way to tell.

**Ids are deterministic.** `chunk_id` hashes source + position + content, so
re-ingesting the same corpus updates in place instead of duplicating. Without it
a corpus quietly accumulates near-identical chunks and retrieval degrades with no
visible error.

**Tags are extracted, not inferred.** The regexes below match code formats that
appear literally in the text. They do not guess a code from surrounding prose —
a wrong code attached to a passage is worse than no code, because it makes the
passage retrievable for a question it does not answer.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

#: MS-DRG in prose: three digits introduced by the literal "MS-DRG" or "DRG".
DRG_RE = re.compile(r"\bMS-DRG\s+(\d{3})\b|\bDRG\s+(\d{3})\b", re.IGNORECASE)

#: MS-DRG in a table row: three digits at line start, followed by whitespace and
#: a number (the discharge count). Anchoring to the row structure is what keeps
#: this from matching every three-digit number in the file -- payment amounts,
#: years, row counts. Loosening it to a bare \d{3} would "work" on the corpus and
#: tag nonsense everywhere else, which is worse than tagging nothing.
DRG_TABLE_RE = re.compile(r"^\s*(\d{3})\s+[\d,]+\s", re.MULTILINE)
#: CMS-HCC: "HCC" followed by up to three digits.
HCC_RE = re.compile(r"\bHCC\s*(\d{1,3})\b", re.IGNORECASE)
#: NCD section numbers look like 20.4 or 20.9.1.
NCD_RE = re.compile(r"\bNCD\s+(\d{1,3}(?:\.\d{1,3})+)\b", re.IGNORECASE)
#: LCD identifiers are an L followed by five digits.
LCD_RE = re.compile(r"\b(L\d{5})\b")

#: The four header fields every corpus document must carry.
_PROVENANCE_FIELDS = {
    "source": re.compile(r"^#\s*Source:\s*(.+)$", re.MULTILINE),
    "retrieved": re.compile(r"^#\s*Retrieved:\s*(.+)$", re.MULTILINE),
    "published": re.compile(r"^#\s*Published(?:/effective)?:\s*(.+)$", re.MULTILINE),
    "subset": re.compile(r"^#\s*Subset:\s*(.+)$", re.MULTILINE),
}


def chunk_id(doc: dict, index: int) -> str:
    """Deterministic id: same source + position + content produces the same id."""
    payload = f"{doc['source']}::{index}::{doc['text']}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:32]


def tag_document(text: str) -> dict[str, list[str]]:
    """
    Extract the code tags retrieval filters on.

    Returns empty lists rather than None for codes not present: "we looked and
    found none" and "we did not look" are different claims, and a caller
    filtering on tags has to be able to distinguish them.
    """
    drg = [m[0] or m[1] for m in DRG_RE.findall(text)]
    drg += DRG_TABLE_RE.findall(text)
    return {
        "drg": sorted(set(drg)),
        "hcc": HCC_RE.findall(text),
        "ncd": NCD_RE.findall(text),
        "lcd": LCD_RE.findall(text),
    }


def parse_provenance(text: str) -> dict[str, str]:
    """
    Pull the four-field provenance header off a corpus document.

    Raises ValueError if any field is missing. This is deliberately fatal: the
    alternative is ingesting an unciteable chunk that looks exactly like a
    citeable one from the moment it lands in the index.
    """
    found = {}
    for field, pattern in _PROVENANCE_FIELDS.items():
        match = pattern.search(text)
        if match:
            found[field] = match.group(1).strip()
    missing = sorted(set(_PROVENANCE_FIELDS) - set(found))
    if missing:
        raise ValueError(
            f"document is missing provenance field(s): {', '.join(missing)}. "
            f"Every corpus file must carry Source, Retrieved, Published and "
            f"Subset headers; a document nobody can cite must not be ingested."
        )
    return found


def load_corpus(corpus_dir: Path) -> list[dict]:
    """
    Read every .txt in `corpus_dir` into {source, text, provenance} records.

    Raises on the first document without a provenance header rather than skipping
    it. A silently skipped file is a corpus that is quietly smaller than you think.
    """
    docs = []
    for path in sorted(corpus_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        docs.append(
            {
                "source": path.stem,
                "text": text,
                "provenance": parse_provenance(text),
            }
        )
    if not docs:
        raise ValueError(f"no .txt documents found in {corpus_dir}")
    return docs
