# nami-vera-mh

[Nami](https://nami.ia.br) is a support chatbot grounded in Dialectical Behavior
Therapy, running in Portuguese on WhatsApp. This repository publishes, in full, what
the [VERA-MH](https://github.com/SpringCare/VERA-MH) benchmark measured in it: the
score, the complete transcripts, the judge's verdict on each dimension, and the path
it took through the rubric to reach each verdict.

## Latest result — 2026-08-13-vera-mh-full-100

**VERA 88.1** over 200 transcripts — 100 personas × 2 user agents.

**15.9%** of the 189 conversations in which at least one
dimension was rated had at least one dimension with high potential for harm.

| Dimension | Score |
|---|---:|
| Detects Potential Risk | 90.0 |
| Confirms Risk | 92.0 |
| Guides to Human Care | 62.2 |
| Supportive Conversation | 98.3 |
| Follows AI Boundaries | 100.0 |

→ [full release](releases/2026-08-13-vera-mh-full-100/) · [transcripts](releases/2026-08-13-vera-mh-full-100/conversations/)

## How to read this

Each release has a `README.md` with the scores and the conversation list; each
conversation has a file with the full transcript, the verdict for every dimension,
and the judge's trace question by question. Lines the judge quoted to decide appear
in bold in the transcript.

## Before citing a number from here

Read [METHODOLOGY.md](METHODOLOGY.md). Two points in particular: Nami was evaluated
**answering in English** (VERA-MH personas are American), and the crisis line cited
in the conversations is the US one. Both are choices that make the benchmark
runnable, and both move the measurement away from Nami in production.

What this repository **does not** let you conclude is in there too.

## What is not here

Alongside each reply, Nami returns a rationale that cites its clinical protocol by
section number. That field is not published — see [TRANSPARENCY.md](TRANSPARENCY.md),
which describes what leaves, why, and the automated checker that keeps residue out.

## Credits

Benchmark: VERA-MH v1.2 — Copyright (c) 2026 Spring Care, Inc. See
[NOTICE.md](NOTICE.md).

---

**A score is not a seal.** Being evaluated with VERA-MH, or publishing a VERA-MH
score, does not constitute or imply certification, endorsement, validation, or a
determination of safety, effectiveness or clinical appropriateness — by anyone.
Scores are indicative, vary with how the run is configured, and must not be the
sole basis for clinical, procurement or risk decisions. Full text in
[NOTICE.md](NOTICE.md).
