# Architecture

How the private system this example is drawn from is built, and which parts are
here.

Everything in the "In this repo" column is runnable in `example/`. Everything in
"Private" is described but not implemented here — the design is public, the
implementation and the evaluation set that tunes it are not.

| Layer | In this repo | Private |
|---|---|---|
| Corpus provenance | ✅ mandatory four-field header | same, at corpus scale |
| Domain routing | ✅ term-scored, explicit fallback | larger vocabulary + cross-collection fusion |
| Chunking | ✅ paragraph-packed | same idea, tuned per document class |
| Dense retrieval | ✅ single model, per-domain collections | domain-tuned models per collection |
| Hybrid lexical (BM25) | ❌ | ✅ |
| Query expansion / HyDE | ❌ | ✅ |
| Reranking | ❌ | ✅ |
| Verification receipt | ❌ described below | ✅ |
| Gap flywheel | ❌ described below | ✅ |
| Evaluation suite | ❌ | ✅ |

---

## 1. Provenance is an ingestion precondition

Most retrieval systems treat provenance as metadata: nice to have, attached when
available. This one treats it as a gate. `parse_provenance()` raises if a document
lacks Source, Retrieved, Published or Subset, and `load_corpus()` does not catch it.

The reasoning is asymmetric risk. A document with no provenance is not merely less
useful than one with provenance — **it is indistinguishable from one that has it**
once both are chunks in an index. There is no later point at which you can sort them
out, because the information needed to sort them was discarded at ingestion.

The `Subset` field matters more than it looks. "All 14 national rows" and "top 30 by
discharge volume" are different claims about the same dataset, and a reader who does
not know which one they have will over-generalise from a partial extract. One of the
corpus documents here is explicitly an *index only* — the policy bodies were excluded
because they carry licensed content — and the header says so, so no reader mistakes
it for the full policy.

## 2. Route before you retrieve

A single flat index over mixed clinical content will answer a coverage question out
of a coding document. The passages are topically adjacent, the embedding distance is
small, and the answer is wrong in a way that reads fluently.

Splitting the corpus by domain and routing the query to one collection is the
cheapest available fix, and it is most of what fancier retrieval architectures are
actually buying.

**The fallback is the design decision, not the routing.** `route()` returns `general`
when no domain scores, rather than returning the best of a bad set. A router that
always picks a winner has thrown away the fact that it did not recognise the query —
and that fact is exactly what tells you the answer needs more scrutiny.

This is the same principle as the receipt in §4: a system that cannot say "I do not
know" will say something else instead.

## 3. Entity tagging, anchored to structure

Tags are extracted from formats that literally appear in the text: `MS-DRG 871` in
prose, `871  578,073` as a table row, `HCC 37`, `NCD 20.4`, `L33822`.

The table-row pattern is worth a note because it is where a permissive regex is
tempting. The MS-DRG corpus file lists codes as line-anchored rows, so a prose-only
pattern found *one* code in a file listing thirty. The obvious fix — match any
three-digit number — would have worked on this corpus and tagged payment amounts,
years and row counts as DRG codes everywhere else.

**A wrong tag is worse than a missing tag**, because it makes a passage retrievable
for a question it does not answer. The pattern anchors to row structure instead, and
a test pins that a bare three-digit number is not tagged.

## 4. The verification receipt — described, not implemented

The private system does not return a bare answer. It returns:

- **the answer**
- **provenance** — which passages supported it, with their sources and dates
- **a confidence tier** — a cross-encoder judgement of whether the retrieved
  passages *address the question*, not of how near they sit in embedding space
- **a gap signal** — raised when the retrieved passages do not support an answer

The gap signal is the part that matters and the part most systems omit. A retrieval
system's dangerous failure is not returning nothing; it is returning something
plausible. An explicit "the corpus does not support this" is a different output from
a low-confidence answer, and conflating them is how unsupported claims reach users
wearing the same formatting as supported ones.

**Why relevance and not similarity.** This was measured, and the first answer was
wrong. Thresholding on retrieval distance produced one reachable tier: over a
sample of in-domain queries the similarity score never left a narrow band, so
every query graded "high" and the gap signal could not fire. Questions the corpus
cannot answer at all graded "high" too. Cross-encoder relevance on the same
queries separated cleanly where similarity did not — the difference between "is
this text nearby" and "does this text answer the question". The demo transcript
shows the consequence directly: two queries there retrieve the *identical*
passage with identical citations and receive opposite verdicts.

A note on confidence labels, learned expensively: a label is only meaningful if it
can be *false*. The private system once had a `derived` tier documented as "traced to
a published source" that was awarded by membership in a local lookup table — so it
was assigned precisely when the number was unsourced. A label with no true instances,
applied to most rows, is not a label. It is decoration.

## 5. The gap flywheel — described, not implemented

When a query produces a gap signal, it does not just get logged. It becomes an
ingestion target: the corpus grows along the axis where it was demonstrably weakest,
and the next equivalent query is answerable.

That is the compounding loop, and it is the reason the evaluation set is not
published. The patterns above are recoverable by any competent engineer. What is not
recoverable is a corpus that has been shaped by its own measured failures over time,
and the eval set that measures them.

## 6. What plain dense retrieval actually gives you

The example in this repo returns the right **document** reliably and the right
**passage** less reliably. Ask it which MS-DRG had the most discharges and it routes
to `coding`, retrieves the right file, and often surfaces the column-definition chunk
above the data row — because a passage explaining what "total discharges" means is
genuinely semantically close to a question about total discharges.

Three techniques are conventionally applied to close that gap:

1. **Hybrid lexical retrieval.** A BM25 component catches exact-token matches — a
   DRG code, an L-number — that dense embeddings blur.
2. **Reranking.** A cross-encoder over the top-k reorders passages by relevance to
   the query rather than by embedding proximity.
3. **Query expansion.** Generating a hypothetical answer and retrieving against
   *that* pulls in passages phrased like answers rather than like questions.

None are in this repo, and their absence is a scope decision rather than a secret —
all three are ordinary published techniques.

**But do not read that list as a recommendation, because it did not survive
measurement.** In the private system, both (1) and (2) were measured and both *cost*
precision rather than adding it — the BM25 hybrid merge substantially so at the
smallest context budgets. RESULTS.md has the numbers and the decomposition that
attributes the loss.

That is worth stating plainly rather than quietly omitting: the received wisdom
about these layers is not wrong in general, and it was wrong here. Which layer helps
is a property of a corpus and a query distribution, not of the technique — and the
only way to know is the ablation.

---

## Claims measured on the private system

Everything below is a statement about a system you cannot run from this repo, and is
labelled as such rather than demonstrated here.

- The private system carries an evaluation suite spanning multiple clinical and
  regulatory domains. *(An earlier draft called it "substantially larger than is
  typical for its class". That is a comparative claim about other people's systems
  and nothing here measures them, so it has been withdrawn.)*
- Its tiered ablation has been re-measured following a corpus remediation that
  removed a large volume of unsourced documents. **The figures are in RESULTS.md**,
  along with the two harness bugs that produced plausible wrong numbers first and
  the reason the headline result is a negative one.

The pre-remediation figures are not quoted anywhere in this repo. It would be easy
to quote the pre-
remediation numbers, and they were better. They were also measured against a corpus
that no longer exists.
