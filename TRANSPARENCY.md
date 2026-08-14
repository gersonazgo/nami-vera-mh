# What is not published, and why

A results repository that omits things silently is no good for checking anything.
This document states what leaves here, what stays out, for what reason, and how
you can verify the rule was followed without taking our word for it.

## What is published

- **The full transcripts**, turn by turn, uncut and unedited.
- **Every judge verdict**, with its reasoning and the quotes it relied on.
- **The complete trace**: each rubric question the judge asked, the answer, the
  reasoning, and where that answer led in the flow.
- **The synthetic persona prompts** — who the simulated patient was playing.
- **The score**, the per-dimension percentages, and the `results.csv` that
  produces them.
- **The cost**, by role and by model.

## What is not

**Nami's clinical prompt.** It is the protocol the product executes; it is not
public.

**Nami's `reasoning` field** — the rationale it returns alongside each reply.
This one needs explaining, because it is not obvious.

Nami is instructed to cite, in its reasoning, the clause of the protocol it
relied on. Each rationale names one or more sections by number and states what
that section requires at that moment — something of the form *"clause N requires
doing X before Y"*, with the real clause number in place of N.

One such rationale is interesting. Two hundred of them are the structure of the
protocol: the numbering, the hierarchy, which triggers fire what, in what order.
Publishing the transcripts shows **what** Nami did; publishing the rationales
would hand over **the document** that tells it to. That is where the line is.

The **judge's** reasoning is published — it comes from GPT-5.4, evaluates against
a rubric that is public, and is the most useful content in this repository.

**File paths from the machine that ran the benchmark**, and per-API-call
telemetry (one entry per request). The first is accidental leakage of a username;
the second is internal accounting that does not help anyone check the score.

## How this is enforced

Not by manual review. Generating this repository runs a checker with four layers,
and it runs **before** any file is written — if it flags something, nothing is
published.

| Layer | What it does |
|---|---|
| **Schema** | The public object is assembled by picking fields, not by deleting forbidden ones. A field added in the future simply does not come out until someone decides it may. |
| **Structural** | Flags any `reasoning` that is not in exactly the two places where it belongs to the judge. The rule is by path, not by field name — "no reasoning anywhere" would be the wrong rule. |
| **Textual** | Searches for local file paths, section citations in the three formats they appear in, the internal names of Nami's tools, and secret patterns. |
| **Prompt shingles** | Extracts every 8-word sequence from the clinical prompts and looks for each one in the published bytes. It backs the verifiable claim: *no 8-word passage of the protocol appears here.* |

The first layer is preventive and lives in the generator; the fourth runs only on
the machine that generates the repository — it needs the prompt to work, and
publishing even its hashes would be partial leakage. The middle two run again in
this repository's CI, on every push, from a copy of the checker itself in
[`tools/leak_gate.py`](tools/leak_gate.py) — 230 lines, standard library only,
meant to be read. The redaction rules are therefore public and auditable: you can
read what was removed and how.

The checker has tests, and one of them builds a deliberately poisoned tree to
prove it fails. A checker never seen failing is a claim, not a guarantee.

## If you find something that should not be here

Open an issue. A leak is a defect, and the defect matters more than the score.
