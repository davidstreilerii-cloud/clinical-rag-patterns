# Results

**Methodology is published here. Figures are not, and the reason is the interesting
part.**

## Why there are no numbers on this page

The private system's tiered ablation previously carried headline accuracy figures.
Those figures were measured against a corpus that has since had a large volume of
unsourced documents removed — content that had entered through a fetch pipeline
which fell back to hardcoded literals when a source was unreachable, and which for
several sources never attempted a fetch at all.

Quoting the old numbers would be quoting a measurement of a corpus that no longer
exists. Re-running the ablation does not reproduce them; it establishes a **new
baseline**.

**The direction of that change is genuinely unknown, and worth stating plainly:**

- Accuracy may **rise**, because a class of confidently-wrong answers sourced from
  invented content is now impossible.
- Accuracy may **fall**, because some evaluation questions were only answerable from
  the removed content, and the honest response to those is now "the corpus does not
  support this."

The second outcome would be a *better* system scoring worse, which is precisely why
the number cannot be reported without the context.

## The methodology

Three tiers, defined so that the harness and any report of it cannot drift apart:

| Tier | Configuration |
|---|---|
| **A** | Full stack: domain routing, hybrid lexical + dense retrieval, query expansion, receipt gating |
| **B** | Public-equivalent: domain routing, plain dense retrieval. No receipt, no expansion, no reranking. This is what `example/` in this repo does. |
| **C** | No retrieval. The model answers from parameters alone. Floor. |

Scoring is token-overlap recall against ground truth at a fixed threshold —
deliberately lenient, because retrieval answers paraphrase heavily and an exact-match
scorer measures phrasing rather than correctness.

**What A−B measures** is the value of the machinery that is not in this repo. **What
B−C measures** is the value of retrieval at all, which is the less interesting number
and usually the larger one.

## The evaluation set is not published

Not as a hedge — the set is the asset. The retrieval patterns in this repo are
recoverable by any competent engineer from the code and ARCHITECTURE.md. A corpus
shaped over time by its own measured failures, and the query set that measures them,
is not.

Publishing the *deltas* without the set is the honest middle: it says what the
machinery is worth without handing over the instrument that measured it. That is the
intent for this page once the re-measurement is done.

## Reproducibility

The example in this repo is fully reproducible — clone it, run the tests, run a
query. Anything stated about the private system is labelled as such in
ARCHITECTURE.md and is not reproducible from here, which is a limitation worth
stating rather than obscuring.

Results on the private system available on request.
