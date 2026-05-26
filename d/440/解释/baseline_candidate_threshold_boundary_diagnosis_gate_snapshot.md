# v440 baseline-candidate threshold boundary diagnosis gate page snapshot

Playwright MCP was attempted first, but the MCP transport was closed in this session. The final visual evidence was captured with Playwright CLI using the local Chrome channel against a temporary local HTTP server.

Observed page structure:

- main
  - heading: `MiniGPT baseline-candidate threshold boundary smoke`
  - section: `Summary`
    - Status: `pass`
    - Decision: `review`
    - Source mode: `reuse_summary`
    - Gate mode: `diagnosis_strict`
    - Expected exit: `2`
    - Smoke: `pass`
    - Matrix: `pass`
    - Thresholds: `3`
    - Accept count: `0`
    - Reject count: `3`
    - Boundary: `review`
    - Diagnosis: `candidate_not_accepted`
    - Strictest accept: `none`
    - First reject: `0.0`
    - Monotonic: `True`
  - section: `Diagnosis`
    - Issue count: `1`
    - Action count: `2`
    - Issue: `no_accepting_threshold`
    - Actions: `increase_candidate_signal`, `keep_current_baseline`

Evidence screenshot:

```text
d/440/图片/01-baseline-candidate-threshold-boundary-diagnosis-gate.png
```
