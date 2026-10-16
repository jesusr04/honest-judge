# Research decisions (2026-10-16)

Source: `research/2026-10-16-deep-research-report.md` (MT-Bench, JudgeBench, BIPIA, Spotlighting, StruQ, Instruction Hierarchy, G-Eval, Prometheus, calibration studies).

| Finding | Decision | Status |
| --- | --- | --- |
| Candidate-as-data framing + authority hierarchy cuts injection success | Adopted in prompt v1.1.0 | Done |
| Solve independently before reading the candidate (MT-Bench) | Adopted in v1.1.0 | Done |
| Criterion decomposition preserving AND/OR/NOT | Adopted in v1.1.0 + logic cases | Done |
| Verbalized confidence runs overconfident; 0.99 hurts Brier when ~90% right | Top band lowered 0.97 → 0.93 | Done; replace with measured buckets |
| Structured reasoning + verdict/reasoning audit for appeals | Adopted in v1.1.0 | Done |
| Endpoint: AB + BA in parallel, agree → verdict, else tie | Endpoint v2 | Planned |
| Endpoint: cache by input hash → identical repeats | Endpoint v2 | Planned |
| Endpoint: provenance-mark candidate lines + reminder after data | Endpoint v2 | Planned |
| Temperature 0 | Not possible: current Claude models reject sampling params. Determinism via cache instead | Rejected |
| Majority vote of 3+ samples | Doesn't fix injection (correlated failures); AB/BA is better for pairwise | Rejected |
| Two-pass extract-then-grade | Only if injection suite shows misses | Deferred |
