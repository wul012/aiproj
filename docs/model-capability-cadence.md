# Model Capability Cadence

Publication receipt and maintenance versions are useful, but they do not prove model improvement. MiniGPT should periodically return to model capability evidence after several governance or maintenance versions.

Recommended cadence:

- After three to four publication receipt or readability maintenance versions, schedule a focused model capability regression.
- Prefer small, reproducible checks over vague claims.
- Candidate checks include holdout accuracy, exact surface repair, required term coverage, loss signal bridge, unassisted repair, and decoder anchor distribution.
- A pass in publication receipt governance should never be treated as a training improvement.

The v1133 checker reads recent README version sections and warns when the leading run of non-capability versions exceeds the configured limit.
