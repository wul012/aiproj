# MiniGPT Required-Term Pair Equals-Surface Repair Comparison

- Status: `pass`
- Decision: `required_term_pair_equals_surface_branch_competition_detected`
- Compared reports: `2`
- Branch competition seeds: `1`
- Pair-full profile seeds: `0`
- Union hit terms: `fixed,loss`

## Source Reports

| Label | Status | Corpus mode | Pair-full seeds | Source |
| --- | --- | --- | ---: | --- |
| v552-fixed-repair | pass | equals_surface_fixed_repair | 0/1 | e\552\解释\model-capability-required-term-pair-equals-surface-fixed-repair\model_capability_required_term_pair_colon_immediate_stability.json |
| v554-balanced-repair | pass | equals_surface_balanced_repair | 0/1 | e\554\解释\model-capability-required-term-pair-equals-surface-balanced-repair\model_capability_required_term_pair_colon_immediate_stability.json |

## Branch Rows

| Seed | Competition | Fixed hit reports | Loss hit reports | Pair-full reports | Next action |
| --- | --- | --- | --- | --- | --- |
| 1535 | True | v552-fixed-repair | v554-balanced-repair |  | tie fixed/loss branches in one objective or isolate branch prompts before another full seed sweep |

## Term Evidence

| Report | Seed | Profile | Term | Hit | Prompt | Preview |
| --- | --- | --- | --- | --- | --- | --- |
| v552-fixed-repair | 1535 | default | fixed | False | fixed= | fi\nfixeq\nfix |
| v552-fixed-repair | 1535 | suppress_newline_tokens | fixed | True | fixed= | fixed=fixed= |
| v552-fixed-repair | 1535 | default | loss | False | loss= | fiossssss=fs |
| v552-fixed-repair | 1535 | suppress_newline_tokens | loss | False | loss= | fiossssss=fs |
| v554-balanced-repair | 1535 | default | fixed | False | fixed= | loss=los=ss= |
| v554-balanced-repair | 1535 | suppress_newline_tokens | fixed | False | fixed= | loss=los=ss= |
| v554-balanced-repair | 1535 | default | loss | True | loss= | loss=losss=l |
| v554-balanced-repair | 1535 | suppress_newline_tokens | loss | True | loss= | loss=losss=l |

## Boundary

- Model quality claim: `diagnostic_only`
- Reason: The compared repairs cover fixed and loss across runs, but no single run/profile keeps both terms together.
- Next action: tie the two branches in one objective or isolate prompt branches before spending more seed budget
