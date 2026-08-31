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

## The recall-anywhere result, and why it needed a second experiment

At the full candidate set, the tiers are **identical** — 215 of 250 each. That is
not because the machinery is worthless; it is because the metric cannot see it. Both
layers Tier A adds are *ordering* operations, and a scorer asking whether ground
truth appears *anywhere* in the set is order-insensitive.

So the first experiment could not answer its own question. The second one can.

## precision@k — what each layer is actually worth

Scoring the same ordered results at shrinking k makes position matter. **k is not an
abstraction: it is how many chunks fit in a generator's context budget.**

| tier | k=1 | k=3 | k=5 | k=10 | k=20 |
|---|---|---|---|---|---|
| **B** plain dense retrieval | **67.20** | **79.20** | **84.00** | **86.00** | 86.00 |
| **R** + cross-encoder reranking | 64.40 | 76.00 | 80.80 | 84.80 | 86.00 |
| **H** + BM25 hybrid merge | 36.00 | 78.80 | 84.80 | 86.00 | 86.00 |

Both added layers **cost** precision rather than adding it, and the columns converge
by k=20 exactly as they must, since all three see the same candidate set.

**BM25 hybrid merge is the larger problem**: 67.20 → 36.00 at k=1, a 31-point loss.
Reciprocal-rank fusion is demoting the chunk dense retrieval had ranked first.

**Reranking costs a few points at every k.** That is a real result and it is not the
one anybody expects from a cross-encoder.

### Reranking was not running at all until this experiment

The rerank function opened with a guard that returned early when the candidate count
did not exceed the requested budget, on the stated premise that there was "no
benefit" in that case. The premise is wrong — reranking *reorders*, and order is the
whole product. The production caller passes a budget of 10, so **every retrieval
returning ten or fewer chunks skipped reranking silently** while the call site read
as though it had reranked.

It was caught by measurement rather than by reading: a rerank-only tier scored
identically to plain dense retrieval at *every* k, to two decimal places. Identical
to two decimals across the whole sample is the signature of a component that is not
running, not one that is not helping.

The numbers above are from after the fix. Before it, that row was indistinguishable
from the baseline.

### A measured but unproven explanation

The reranker scores only the first 512 characters of each chunk. The median retrieved
chunk is 676 characters and **53% exceed 512**, so it ranks on partial text that the
scorer then evaluates in full. That is a plausible cause of the degradation. It is
**not proven** — confirming it needs a run with a wider window, which has not been
done, so this page does not claim it as the answer.

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
