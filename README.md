# clinical-rag-patterns

Retrieval patterns for regulatory and clinical documents, extracted from a private
production system and reduced to something you can read in ten minutes and run in
three commands.

This is the public layer of a system that is not public. That framing is deliberate
and the section at the bottom says exactly what is missing and why.

---

## What is here

A working retrieval example over **eight genuinely-sourced CMS documents** — MS-DRG
national utilisation, CMS-HCC v28 risk-adjustment coefficients, National and Local
Coverage Determinations, readmissions, healthcare-associated infections,
complications and mortality, and timely-and-effective-care process measures.

Every document carries a four-field provenance header:

```
# Source: https://data.cms.gov/provider-data/api/1/datastore/query/cvcs-xecj/0?...
# Retrieved: 2026-08-20
# Published/effective: released 2026-08-13, modified 2026-07-22, issued 2020-12-10
# Subset: all 14 national rows
```

Ingestion **refuses** a document without one. That is the single most load-bearing
decision in this repo, and the reason is in ARCHITECTURE.md.

## Run it

Python 3.12. From the repo root:

```bash
pip install chromadb sentence-transformers pytest
python -m pytest example/tests/ -q
python -m example.retrieve "national 30-day readmission rate for heart failure"
```

The first run downloads a ~90 MB embedding model and builds a local Chroma index
under `example/chroma/` (gitignored). Re-running is idempotent — ids are
deterministic, so a second pass updates in place rather than duplicating.

Output carries provenance through to the answer:

```
Query:     national 30-day readmission rate for heart failure
Routed to: quality

--- 1. cms_readmissions_national  (distance 0.4667)
    source:    https://data.cms.gov/provider-data/api/1/datastore/query/cvcs-xecj/0?...
    retrieved: 2026-08-20
    ...
```

## The three patterns

**Route before you retrieve.** A single flat index over mixed clinical content
answers coverage questions out of coding documents. Splitting by domain and routing
to one collection is cheap and does most of the work fancier retrieval gets credit
for. `example/route.py`.

**Make the fallback explicit.** `route()` returns `general` when nothing matches,
rather than the highest-scoring domain. A router that always picks a winner will
answer a coverage question from the coding corpus and sound confident doing it.
"I do not know which domain this is" is information — discard it and you cannot
distinguish a routed answer from a guessed one.

**Carry provenance to the answer, not just to the index.** Every returned passage
knows its source URL, retrieval date and stated subset. A passage that cannot be
cited is not merely less useful than one that can — it is *dangerous*, because it
looks identical.

## What's deliberately not here

This is the part worth reading closely.

**No confidence scoring, no verification receipt, no gap signal.** The private
system returns an answer bundled with its provenance, a confidence tier, and a flag
when it could not answer — and routes that flag into an ingestion queue so the
corpus grows along the axis where it was weakest. ARCHITECTURE.md describes the
design. The implementation, the evaluation set that tunes it, and the loop that
compounds it are not published.

**No relative weights, and no reimbursement arithmetic.** MS-DRG relative weights
live in Table 5 of the IPPS Final Rule, a spreadsheet attached to the rule and
revised annually. They are not in this repo and the example does not estimate one.
Neither is there a "base rate" — the IPPS base operating rate is federal, then
adjusted per facility by wage index, IME, DSH and outliers, so the rate that applies
is that hospital's.

**No LCD or NCD policy text.** The coverage documents here are *indexes* — code,
title, contractor, effective date. LCD policy bodies carry AMA-licensed CPT content,
so the fetch that built this corpus deliberately excluded the indication, coding-
guideline and documentation-requirement fields, and the contractor street address,
phone, fax and named medical director along with them.

**No evaluation queries.** The private system's suite is not published. RESULTS.md
describes the methodology.

**No claim this example is production retrieval.** It is plain dense retrieval with
no hybrid lexical component and no reranking, and it behaves accordingly: it returns
the right *document* reliably, and the right *passage* less reliably — a schema or
definition chunk often outranks the data row you wanted. That gap is exactly what
the additional machinery closes, and showing it honestly is more useful than hiding
it behind a tuned demo query.

## Provenance, and why this repo is careful about it

The private system this comes from shipped fabricated reference data for months. A
fetch script fell back to hardcoded literals when a source was unreachable — and for
several sources no fetch was ever attempted — so invented values reached users
wearing federal attribution. Invented Medicare coverage criteria were published under
real LCD numbers that belong to entirely different clinical topics.

That was found, and the remediation is why several of the rules in this repo look
stricter than they need to be for eight documents: ingestion refuses undocumented
sources, tagging is structure-anchored rather than permissive, and the example
declines to compute figures it cannot source.

If you take one pattern from this repo, take that one. A retrieval system's failure
mode is not returning nothing. It is returning something plausible.

## Licence

See LICENSE.
