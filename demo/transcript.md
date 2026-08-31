# Demo transcript

A real session against the private system, run **2026-08-31**. Every line below
was produced by that run — nothing is reconstructed, and nothing is trimmed
without being marked.

Five revenue-cycle questions. The point of the selection is not that the system
answers all five. It is that it answers three, and says so when it cannot answer
the other two — for two *different* reasons.

Passage text is abbreviated to the first line and marked `[…]`. Nothing else is
removed.

---

### 1. National 30-day readmission rate for heart failure

**Confidence: high** · 5 passages · one retrieval pass

> National Benchmark: 30-Day Heart Failure Readmission Rate — Hospital Quality
> Source: CMS Hospital Compare (2025). Risk-adjusted 30-day all-cause readmission
> following HF […]

The straightforward case. The corpus holds the benchmark, retrieval finds it, and
the passage addresses the question asked.

---

### 2. Which MS-DRG had the highest number of Medicare discharges nationally?

**Confidence: good** · 5 passages · regulatory anchors found: 3

> CMS Provider Utilization and Payment Public Data — CMS releases annual Medicare
> Fee-for-Service claims summaries by provider and MS-DRG (inpatient) or HCPCS
> (outpatient). […]

Note the tier. The system retrieved a passage describing *where this data lives*
rather than a passage stating *the answer*, and graded itself accordingly. That
distinction is the entire reason the tier exists — "I found the right dataset" and
"I found the answer" are different claims.

---

### 3. What is the difference between a national and a local coverage determination?

**Confidence: high** · 5 passages · anchors: `42 CFR 405.201`, `42 CFR 426.500`

> CMS National Coverage Determination (NCD) vs Local Coverage Determination (LCD) —
> Differences and Hierarchy. National Coverage Determination (NCD): A nationwide
> Medicare […]

---

### 4. Does Medicare have a national coverage determination for TAVR?

**Confidence: uncertain — gap raised** · 5 passages · anchors: `42 CFR 405.201`, `42 CFR 426.500`

> CMS National Coverage Determination (NCD) vs Local Coverage Determination (LCD) —
> Differences and Hierarchy. National Coverage Determination (NCD): A nationwide
> Medicare […]

**This is the interesting one, and it is why the transcript exists.**

Compare it with query 3. **Identical top passage. Identical regulatory citations.
Opposite verdicts.**

The passage explains what an NCD *is*. That fully answers question 3. It says
nothing about transcatheter aortic valve replacement, so it does not answer
question 4 at all — and retrieval similarity cannot tell those two situations
apart, because the same text is equally *near* both queries.

The corpus does contain TAVR material. Retrieval simply surfaced the wrong thing,
and only one of the five returned passages mentioned the procedure. So this is a
**retrieval failure that the receipt caught**, not a missing-data problem — and it
is exactly the case that becomes an ingestion and retrieval target rather than an
answer.

**Before this mechanism was recalibrated, on 2026-08-31, this query returned
"high" confidence with those two real CFR citations attached.** A correct-looking
answer, correctly cited, built on a passage that does not address the question.
That is the failure mode the receipt exists to prevent, and it was live until it
was measured.

---

### 5. How many CLABSI events did a named hospital report in Q3 2025?

**Confidence: uncertain — gap raised** · 5 passages · anchors: none

> IRS Form 990 financial profile — a *differently named* hospital. Source:
> ProPublica Nonprofit Explorer. Most recent filing: tax year 2023 […]
>
> *(Trimmed: the passage continues with that organisation's public financial
> summary. The hospital's name and identifiers are withheld here — the source is
> public, but reproducing a named organisation's record in a demo is not
> necessary to make the point.)*

The second kind of failure, and a different one from query 4. Facility-level
infection counts for a specific quarter are data this system has never held. There
is nothing to retrieve, so retrieval reached for the nearest thing in embedding
space — a *similarly named* hospital's tax filing.

An answer generated from that passage would have been confidently, fluently, and
completely wrong. The gap signal is what stops it.

---

## What the five queries demonstrate

| | |
|---|---|
| **high** | the corpus answers the question |
| **good** | the corpus is adjacent — right dataset, not the answer |
| **uncertain (4)** | the answer exists but retrieval missed it → *retrieval* target |
| **uncertain (5)** | the answer was never held → *ingestion* target |

Four distinguishable outcomes, and the two failures are separated by cause rather
than lumped into one "low confidence" bucket. A system that returns the first
three and silently guesses at the last two looks *better* on any accuracy metric
and is considerably more dangerous.

## Honest notes on this transcript

- **It was generated after a fix, not before.** Until 2026-08-31 the confidence
  mechanism was thresholded on retrieval distance, which in a dense single-domain
  corpus does not vary enough to discriminate — every query returned "high" and
  the gap signal could not fire. It was recalibrated onto a cross-encoder
  relevance judgement, with thresholds fitted to a measured distribution. Queries
  4 and 5 would both have read "high" the day before.
- **Query 2's "good" is a real grade, not a hedge added for this document.** The
  run produced it.
- **The retrieval failure in query 4 is a genuine defect**, shown rather than
  edited out. The corpus holds TAVR material and retrieval did not surface it.
- **No dollar figures appear anywhere in this transcript.** The private system
  withholds financial estimates that rest on unverified reference data; see
  RESULTS.md and the "what's deliberately not here" section of the README.
