# README Exhibition Brief — one engineering-lane version (authorized 2026-07-13)

NOTE ON TIMING: written while v1277 (capacity squeeze) is in flight; this brief is
executed AFTER v1277 closes, as its own version — never mixed into a science version.

Goal: the GitHub landing page (wul012/aiproj) should exhibit this repo's real product —
**a catalog of preregistered, reproducible toy-scale ML science** — in 30 seconds.
Repo description and topics are already set on GitHub.

Hard constraints:
- The honest-measurement gate and docs-honesty conventions bind: the "model quality is
  educational" boundary and the no-promotion boundary stay verbatim; every claim links
  to a version doc, test, or cached artifact; scope labels ("toy scale, own substrate")
  appear wherever results are summarized.
- ML lane untouched (this is an engineering-lane docs version); elegance gates apply;
  coverage/name/size gates must stay green.

## Target structure for `README.md`

1. Badge row:
   `[![CI](https://github.com/wul012/aiproj/actions/workflows/ci.yml/badge.svg)](https://github.com/wul012/aiproj/actions/workflows/ci.yml)`
   plus shields.io static badges: tests `3500+`, coverage floor `≥88.98`, name-budget
   violations `0 new`.
2. Hero (EN + 中文): from-scratch MiniGPT lab; two lanes (science cadence + governance
   engineering); the method IS the product — preregister-commit-then-run, Phase A/B
   caching, decide() contracts, honest nulls.
3. **The science catalog table** (the exhibit's centerpiece): one row per closed
   axis — version(s) · question · verdict · one-line finding — from LoRA/SFT/DPO
   through distillation, PTQ, grokking→Fourier circuit (causal), calibration,
   continual learning trilogy, induction mechanism (QK+OV), double descent (honest
   null), wd noise rejection, Fourier lottery ticket (frequency-sparse but
   magnitude-dense), superposition (adjudicated), capacity squeeze (v1277). Each row
   links to its `docs/v12XX-*-brief.md` or version walkthrough. Verdicts quoted
   exactly (including nulls and review branches — the nulls are selling points, not
   embarrassments).
4. "How to trust a result here" section: the five house rules in one paragraph each
   (preregistration, CPU probes, multi-seed, byte-stable re-derivation from cache,
   external adjudication), with the reproduce-a-verdict quickstart:
   `python -B scripts/analyze_fourier_ticket_v1275.py` (zero retrain).
5. Engineering lane one-liner + links: A-track final evidence, gates, schema registry.
6. Boundaries: educational model quality, toy scale, no-promotion — verbatim.

## Ritual

One version (post-v1277): full suite green, commit/push, CI green, cleanup gate.
Manual follow-up for the user: GitHub Settings → Social preview image.

## Fail conditions

- Any verdict paraphrased into something stronger than its decide() output = fail.
- A catalog row without a link to committed evidence = fail.
- Executed before v1277's close commit = fail (no mixing with a science version).
