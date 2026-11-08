# Run NERVE on a real project: pilot protocol

This guide is for developers who already have a project with a meaningful history, not a synthetic toy repository. The goal is to measure improvements **without claiming them in advance**.

## A. Isolate the test

Choose a non-sensitive local project or a sanitized clone. Back up the original. Use a unique test branch. Check that `.nerve/` is ignored by Git. Do not connect production credentials or private customer records. Do not tell agents the hidden answers.

Install the local package with `pip install -e '.[mcp]'`, initialize the project, and run `scan`. Generate the host MCP config with `cursor-config --write` or supply the equivalent to your supported agent host. Confirm that the server is running before evaluating; MCP tool availability is a prerequisite, not an outcome.

## B. Create repeatable tasks

Before experiments, independently choose at least **30 tasks** distributed across:

1. **Context recovery:** What did the prior agent decide, and why? Gold answer comes from project commit/issue evidence.
2. **Target accuracy:** “The thing that throttles retries” refers to which exact file/symbol/object? Label the gold target ID.
3. **Cross-agent continuity:** Agent A investigates or implements a change, closes; Agent B takes over in a separate fresh session. Task completion is judged by the same tests and external reviewer.
4. **Token efficiency:** Capture provider-reported *total input tokens*, *total output tokens*, tool-calling overhead, and completed-task status. Report tokens **per successful task**, not only per prompt.

Use at least 10 negative or ambiguous target references. Include renamed files, stale memory, incorrect notes, and unsupported requests as hard cases.

## C. Three matched conditions

| Arm | Prior context the agent can access | Restriction |
| --- | --- | --- |
| No memory | Current permitted source files only | No notes or NERVE |
| Plain notes | Same project, normal Markdown notes | No NERVE MCP |
| NERVE | Same permitted source files, NERVE memory/tools | No extra hidden documents |

Each arm receives the same task and model version. Randomize task order, use fresh sessions, and ensure no leakage between arms. For paired trials use 3–5 repeated runs per task where model sampling varies. Record prompt templates, settings, tool access, and any intervention. Agent A and B may use different models in a separate cross-model stratum.

**Critical fairness:** If NERVE receives rich history from Agent A, plain notes must receive an equivalent amount of actual factual history to avoid measuring *extra information* rather than *better retrieval*. For the no-memory arm clearly identify whether the absence of past history is the condition being measured.

## D. Log each real model trial

The bundled `benchmark.agent_eval` records and scores run logs. It **never calls models itself**. Export a blind question set via `python -m benchmark.agent_eval export`. For a real-project pilot, define your own gold question IDs and adapt the scorer; synthetic fixture IDs are only examples. Use the same row schema: `case_id`, `arm`, `model`, `seed`, `target_id`, `answer`, `input_tokens`, `output_tokens`, `latency_ms`, `agent_a`, `agent_b`, `handoff_completed`.

Use provider usage responses or trusted gateway metrics; a character or word-count estimate is not actual model token usage. Do not infer that a note was used just because it was available.

## E. Score and publish with guardrails

- **Context recovery:** correctly recovered facts / attempted answer queries. Report unsupported-query abstention separately.
- **Target accuracy:** exact Top-1 ID matches / queries with a known answer; separate no-target false-positive rate and Top-3 recall.
- **Cross-agent continuity:** independently judged task success rate and tests passing after session/model handoff; not merely SQLite reopen.
- **Token efficiency:** sum(total input and output tokens) / successful completed tasks; report both tokens and success rate. Do not reward a broken agent for using fewer tokens.
- **Latency:** median and p95 task time, including MCP overhead.
- **Uncertainty:** paired differences per task, Wilson intervals for success proportions, and bootstrap confidence intervals for token differences where appropriate.

Gate suggestion: seek at least **+10 percentage points** on context or handoff success versus *plain notes*, **≥20% fewer tokens per successful task**, with no statistically material regression in exact target accuracy or unsupported-query handling. These thresholds are product goals, not observed improvements. Share all failures and raw non-sensitive trial logs.

## F. Feedback format

```text
Project type:
Local platform / model / version:
How MCP was installed:
Tasks / tasks passed per arm:
Prompt + tool configuration:
Provider-reported tokens per arm:
Target Top-1 / Top-3 / unsupported false-positive rate:
Known failures:
Evidence or minimal reproduction:
```

## Current evidence

`benchmark/results/BASELINE_REPORT.md` documents the v0.3 **synthetic deterministic** baseline. It is not a substitute for this real project protocol. A developer trial should be labeled "real-model" only after an independent agent host actually executes the scenarios and publishes measured usage and outputs.
