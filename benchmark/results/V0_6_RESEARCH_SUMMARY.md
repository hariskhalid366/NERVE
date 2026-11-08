# NERVE v0.6 Research and Dogfood Summary (28 October 2026)

| Experiment | NERVE | Comparator | Scope |
|---|---:|---:|---|
| Original chess reference matching | 38/48 Top-1 (79.2%) | 30/48 Top-1 (62.5%) flat word overlap | In-sample, weights tuned in prior version |
| Additional chess wording stress | 12/24 Top-1 (50%) | 12/24 Top-1 (50%) flat word overlap | Hand-written, same targets/facts as original |
| Unsupported requests on stress set | 8/8 no `supported_candidate` | Not measured | Confirm-or-no-match only; 6/8 return no candidates |
| Evidence revision regression tests | 6 new tests | N/A | SHA-256 source revision, deletion, rescan preservation and migration |
| Python suite | 41 passing | N/A | Unit/integration, no model/provider integration |
| Chess rules engine | 16 passing | N/A | Node tests; not AI chess opponent |
| Clean wheel install | Success | N/A | Offline no-index install + CLI smoke test |

No inference is warranted that NERVE reduces actual provider token usage, improves new agents' ability to finish tasks, or understands indirect references better. The original benchmark is already in-sample; the supplementary test intentionally stresses the known weakness and is not statistically independent of the target list.

The biggest change in v0.6 is safer **reuse of history**: each new target-linked memory/event is bound to a SHA-256 snapshot of its associated source file, and future reads clearly signal changed or missing sources. A hash match is not semantic truth, and old notes without an anchor remain unanchored. Missing source-backed matches are demoted to require confirmation.

See [research review](../../RESEARCH_OCT_2026.md) for sources, experiment design, limitations and next milestones.
