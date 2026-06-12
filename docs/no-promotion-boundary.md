# No-Promotion Boundary

The no-promotion boundary prevents governance evidence from being misread as model quality approval.

In this project, `status=pass` usually means the checked artifact is internally consistent, traceable, and suitable for the stated governance use. It does not automatically mean:

- the model is production ready
- the checkpoint should be promoted
- the generated text quality improved
- the holdout result generalizes beyond the tested scope

Publication receipt reports should keep fields such as `promotion_ready=False`, `approved_for_promotion=False`, bounded `model_quality_claim`, and explicit lookup-only `granted_use` when the evidence is only for governance lookup.

This page is the central wording reference for future maintenance versions, so the same boundary does not need to be rewritten differently in every README entry.
