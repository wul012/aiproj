# MiniGPT Required-Term Pair Surface Variant Plan

- Status: `pass`
- Decision: `required_term_pair_surface_variant_plan_ready`

## Variants

| Variant | Separator | Template |
| --- | --- | --- |
| space_context_control | space | {other_term}={other_term} {term}= |
| semicolon_context | semicolon | {other_term}={other_term}; {term}= |
| newline_context | newline | {other_term}={other_term} {term}= |
| compact_context | compact | {other_term}={other_term}{term}= |
| worded_context | worded | known {other_term}={other_term}; answer {term}= |
