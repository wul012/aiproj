# MiniGPT Model Capability Required-Term Scaffold Probe

- Status: `pass`
- Decision: `required_term_scaffold_probe_ready`
- Probe decision: `explicit_scaffold_still_no_required_term_uptake`
- Probe count: `20`
- Required terms: `20`
- Baseline continuation hits: `0`
- Scaffold continuation hits: `0`
- Prompt truncated: `0`
- Prompt over block: `0`

| Seed | Case | Terms | Baseline hits | Scaffold hits | Block | Prompt chars | Preview |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1337 | classification-risk-level | because | 0 | 0 | 8 | 8 | 判v泛数研据\n能少好保r目rv泛？求方v评少或链 |
| 1337 | comparison-baseline | fixed | 0 | 0 | 8 | 6 | 复请什R研指g每M研四方化据一两否s研指M方ss |
| 1337 | continuation-science | text | 0 | 0 | 8 | 5 | 续开持P洁e四实过变每m是需需有好求的\n问一评两 |
| 1337 | factual-val-loss | loss | 0 | 0 | 8 | 5 | 但但j格数M据否方每问据更工,E和格？评存化一四 |
| 1337 | qa-training-loop | data | 0 | 0 | 8 | 5 | 式风。卡指型研s评少伪？成好否v需少指求泛指链造 |
| 1337 | refusal-boundary | real | 0 | 0 | 8 | 5 | 归l复什同每四s否断两存vmr需需s或是明.工据 |
| 1337 | self-check-missing-data | data | 0 | 0 | 8 | 5 | 现写次s的-采项论研少hg需mv造造MG问a据\n |
| 1337 | structured-experiment-json | four | 0 | 0 | 8 | 5 | 目种y能果损吗vr需目字或链造MM方少好准日准链 |
| 1337 | style-rewrite-concise | while | 0 | 0 | 8 | 6 | 复什能hM该型损？径究研据否的评的seA评否指评 |
| 1337 | summary-evidence-chain | chain | 0 | 0 | 8 | 6 | 简简高G的shh一分好成m或洁e备存指M科v评指 |
| 2026 | classification-risk-level | because | 0 | 0 | 8 | 8 | ii但被型该但路型r现以该准练共成A是很但准路o |
| 2026 | comparison-baseline | fixed | 0 | 0 | 8 | 6 | 类四s共来路少共c该类通否型r高存总要通过过研该 |
| 2026 | continuation-science | text | 0 | 0 | 8 | 5 | 的不论时少补r成g少否时时时练少你时y.路时练少 |
| 2026 | factual-val-loss | loss | 0 | 0 | 8 | 5 | m改常现型否G归构.字存共、种练种时种开实归和该 |
| 2026 | qa-training-loop | data | 0 | 0 | 8 | 5 | 一你常定现定路你y现写你.成g型种路i以wi字、 |
| 2026 | refusal-boundary | real | 0 | 0 | 8 | 5 | 究有查练否时高是很y构被归研归归iT常.字型y以 |
| 2026 | self-check-missing-data | data | 0 | 0 | 8 | 5 | 保类Es是y是c型路准归路路少归固型成r共rr言 |
| 2026 | structured-experiment-json | four | 0 | 0 | 8 | 5 | 你通审样c存s准少时路成T型该是.时否字准y时该 |
| 2026 | style-rewrite-concise | while | 0 | 0 | 8 | 6 | 同伪求y径指共归归实开现以现存高写子备备准Ti类 |
| 2026 | summary-evidence-chain | chain | 0 | 0 | 8 | 6 | 少否G能r实查开有样c存通c准高构s、字、日该r |

## Boundary

- Model quality claim: `not_claimed`
- Reason: Even short prompts that list the required terms did not make the archived tiny checkpoint emit those terms in continuation.
- Next action: run a targeted micro-training repeat with required-term examples before increasing benchmark scope
