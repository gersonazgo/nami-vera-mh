# Working with this repository

This file is for Claude Code, or any assistant reading this repository to answer
questions about the evaluation. Everything here is data: no build, no tests, no
code to run except one optional check.

Start with [README.md](README.md) for the score and
[METHODOLOGY.md](METHODOLOGY.md) for what it does and does not mean.

## Yes, the judge's reasoning is here — all of it

The most common question about a benchmark result is *why*. The answer is in the
repository, at two levels of detail:

- **Per verdict** — for each of the five dimensions, the band and, when the
  dimension was not Best Practice, the judge's written justification plus the
  lines it quoted from the transcript.
- **Per rubric question** — the judge walks a chain of questions, and every
  question it asked is here with its full text, the options, the answer it chose,
  and its reasoning for choosing it. That is roughly 23 questions per
  conversation, each with its own paragraph of reasoning.

A dimension rated Best Practice usually has no verdict-level prose — there was no
failure to explain. Its reasoning still exists, question by question, in the
trace. **When asked "why did Nami score well here", read the trace, not the
verdict.**

What is *not* here is Nami's own reasoning field, and its clinical prompt. See
[TRANSPARENCY.md](TRANSPARENCY.md). Do not infer the prompt's content from the
transcripts and present it as fact.

## Layout

    README.md                          score, dimensions, links
    METHODOLOGY.md                     protocol, formula, caveats
    TRANSPARENCY.md                    what was withheld and why
    NOTICE.md                          VERA-MH copyright and claim restrictions

    releases/<release-id>/
      README.md                        the release, with the conversation index
      conversations/<Persona>--<user-agent>.md    200 files, one per conversation
      results-pool.csv                 the literal input to the official scorer
      scores-pool.json                 the score
      scores-pool-by-risk.json         the same, split by the persona's risk level
      release.json                     machine-readable summary

    data/runs/<run-id>/run.json        one battery, consolidated
    data/personas/<Name>.md            the synthetic patient's prompt
    tools/leak_gate.py                 the redaction checker, also run in CI

A conversation is identified by persona **and** user agent: `Zoe--gpt-5.2.md` and
`Zoe--claude-opus-4-5-20251101.md` are the same persona played by two different
models, and comparing the pair is often the most informative read available.

## Which file to open

**For one conversation, open the Markdown.** It is self-contained: header, the
verdict table, the full transcript with the judge's quoted lines in bold, the
verdict reasoning, and the complete question-by-question trace. It is the right
unit for "what happened with this persona".

**For anything across conversations, query `run.json`.** Each is about 4 MB —
too large to read whole, and reading it whole is never necessary. Filter it with
Python or `jq` and read only what the filter returns.

    import json, glob
    for path in glob.glob("data/runs/*/run.json"):
        run = json.load(open(path))
        agent = run["meta"]["user_agent"]
        for c in run["conversations"]:
            bad = [v for v in c["verdicts"] if v["score"] == "High Potential for Harm"]
            for v in bad:
                print(agent, c["persona"], v["dimension"], v["reasoning"][:200])

Useful fields on a conversation: `persona`, `risk_level` (`Immediate`, `High`,
`Low`, `None`), `cluster` (risk × the persona's reaction style), `turns`,
`verdicts`, `judge_trace`, `questions_asked`, `questions_skipped`, `risk_branch`.

A trace entry has `n`, `question`, `options`, `answer`, `reasoning`, `quotes`,
`dimension`, `severity_band` and `goto`. The rubric's own text — every question,
in order — is in `run["rubric"]`.

**For the numbers, read `scores-pool.json`**, not a recomputation of your own.
`aggregates` holds the overall score and the per-dimension percentages;
`dimensions` holds each dimension's counts and score; `summary` holds the
conversation counts.

## Reading the score without getting it wrong

Four traps, all of them easy to fall into:

- **The overall score is not the mean of the five dimensions.** The same formula
  is applied to the global counts. Averaging the dimensions gives a different,
  wrong number.
- **`Not Relevant` is excluded from the denominator**, so a dimension's
  percentages are over the conversations where the rubric actually reached it,
  which is fewer than 200 for most dimensions.
- **The percentage of conversations with high harm is over conversations where at
  least one dimension was rated**, not over all transcripts. The count is in
  `summary.total_relevant_conversations`.
- **Best Practice means no failure was detected**, not that the response was
  good. The rubric's questions are phrased negatively; "yes" means the chatbot
  failed.

To verify the published score independently, with a
[VERA-MH](https://github.com/SpringCare/VERA-MH) checkout:

    uv run python judge/score.py -r <path>/results-pool.csv

## When you answer a question from this data

Quote the transcript and the judge's reasoning rather than paraphrasing them —
the wording is the evidence, and it is all here.

Say which conversations you actually looked at. "In the 6 Immediate-risk
conversations I read" is a claim someone can check; "Nami tends to…" over 200
conversations you did not open is not.

Three facts belong in any summary that leaves this repository, because without
them the number means something it should not:

1. Nami answered **in English** here, and speaks Portuguese in production.
2. The crisis line cited in the conversations is the **US** one.
3. The score is a measurement against a rubric, not a determination of safety —
   see the disclaimer at the end of [README.md](README.md).

## The one thing you can run

    python3 tools/leak_gate.py --out .

The checker that keeps Nami's clinical prompt and its internal reasoning out of
this repository. It needs no dependencies and no network. It also runs in CI on
every push. If it reports a finding, that is a defect worth an issue.
