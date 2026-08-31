# Results

The headline result of this ablation is a **negative** one, and it is more useful
than the number it replaced.

## The measurement

Three retrieval configurations over the same evaluation suite, the same scorer, and
the same queries:

| Tier | Configuration | Pass rate |
|---|---|---|
| **A** | routing + dense retrieval + BM25 hybrid merge + cross-encoder reranking | **86.00%** |
| **B** | routing + plain dense retrieval — what `example/` in this repo does | **86.00%** |
| **C** | no retrieval | 0.00% \* |

*n = 250, a seeded random sample of the private evaluation suite (seed 20260831). Measured
2026-08-31. Scoring is token-overlap recall against ground truth at a lenient
threshold — retrieval answers paraphrase heavily, and an exact-match scorer measures
phrasing rather than correctness.*

\* **Not measured.** Tier C is 0.0 by construction: the scorer asks whether ground
truth appears in the retrieved chunks, and Tier C retrieves nothing, so the answer is
no for every query against any corpus with any model. It is reported because the
floor belongs in the comparison, but presenting it as a measured result would be
overclaiming.

## A − B = 0.00pp, and why that is the interesting part

The full stack and plain dense retrieval scored **identically** — 215 of 250 each.

That is not because reranking is worthless. It is because **this metric cannot see
it.** Both layers Tier A adds are *ordering* operations: hybrid merge reorders and
deduplicates, reranking reorders. The scorer asks only whether ground truth appears
*anywhere* in the retrieved set. An order-insensitive metric cannot measure
order-optimising machinery.

So A − B here is not a small delta. It is an **unmeasurable** one, and reporting it
as "0.0pp improvement" would be as misleading as reporting a fabricated gain.

Reranking optimises **precision@k** — what reaches a generator's limited context
window, and in what order. Measuring that requires a different experiment: answer
quality under a fixed context budget, or precision at small k. That experiment has
not been run, so this page does not claim a result from it.

## Two bugs found before the number was trusted

Both produced plausible, quotable, wrong figures. They are recorded because the
process is the point.

**Wrong embedding dimensions → 60.00%.** The first version of the harness mapped two
collections to a 768-dimension model when all three are persisted at 1024. The vector
store rejected every query against those collections, retrieval returned empty, and
the scorer counted each as a *failure*. The run completed and printed 60.00%, which
looked entirely reasonable. The correct figure on the same queries was **77.50%**.

The harness now raises if more than 5% of queries retrieve nothing, on the principle
that an empty retrieval is a configuration failure, not a low score.

**Truncation masquerading as a result → "the full stack is worse."** Tier A initially
measured 85.20% against Tier B's 86.00%. One store target maps to two collections, so
Tier B scored up to 20 candidate chunks while Tier A's reranking call truncated to 10.
Against a recall-anywhere scorer, discarding candidates can only lose points. The
0.8pp gap was the truncation, not the machinery — confirmed by instrumenting
per-query chunk counts, then fixed to reorder without truncating.

Had that gone unchecked, this page would have reported that hybrid retrieval and
reranking make the system measurably worse. It would have been a clean, specific,
entirely false finding.

## Sampling

n = 250 is a seeded random sample, not the first 250 drawn in file order. The suite is not
randomly ordered: its first 500 entries contain *all* of one store's queries and
over-weight another at 23% against its true 16%. The seeded draw reproduces the
population within 2 percentage points per store.

A full-suite run was not executed — Tier A runs at roughly one second per query, so
a complete pass is well over the available execution window. **What is reported is what was run**, with its size and seed stated, rather
than a full-suite figure that was not.

## This is a new baseline

Earlier figures for this system were measured against a corpus that has since had
**104 fabricated documents removed** — content that entered through a fetch pipeline
which fell back to hardcoded literals when a source was unreachable, and which for
several sources never attempted a fetch at all.

Those figures are not reproducible and are not comparable to these. One of them was a
4.5-point A−B gap; the measurement above indicates that gap could not have been
produced by this scoring method measuring these layers, so whatever produced it used
a different scorer, different tier definitions, or was never measured.

## The evaluation set is not published

Not as a hedge — the set is the asset. The retrieval patterns in this repo are
recoverable by any competent engineer from the code and ARCHITECTURE.md. A corpus
shaped over time by its own measured failures, and the query set that measures them,
is not.

Publishing the *deltas* without the set is the honest middle. In this case the delta
happens to be zero, and saying so plainly is the whole point.

## Reproducibility

The example in this repo is fully reproducible: clone it, run the tests, run a query.
The tier ablation above was run against the private system and is **not** reproducible
from here. That limitation is stated rather than obscured.
