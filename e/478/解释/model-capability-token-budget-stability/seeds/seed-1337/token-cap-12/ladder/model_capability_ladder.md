# MiniGPT Model Capability Ladder

- Status: `pass`
- Decision: `capability_ladder_ready`
- Trend decision: `loss_improved_without_eval_improvement`
- First max iters: `1`
- Last max iters: `4`
- Best loss max iters: `4`
- Best score max iters: `1`
- Best val loss delta: `-0.0031`
- Score delta: `0.0`
- Generation flags delta: `0.0`

| Max iters | Status | Best val loss | Final val loss | Score | Gen flags | Checkpoint |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | pass | 5.345132350921631 |  | 90.67 | 0 | True |
| 4 | pass | 5.3419880867004395 |  | 90.67 | 0 | True |

## Boundary

- Model quality claim: `not_claimed`
- Reason: This ladder uses tiny CPU runs to observe training-signal movement; it is not robust production model quality evidence.
