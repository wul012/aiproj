# MiniGPT model capability route promotion bounded real replay decoder anchor rebalanced profile sweep

- Status: `pass`
- Decision: `model_capability_route_promotion_bounded_real_replay_decoder_anchor_rebalanced_profile_sweep_no_recovery`
- Ready: `True`
- Best profile: `greedy_short`
- Best passed cases: `0/5`
- Any profile recovered: `False`
- Promotion ready: `False`
- Model-quality claim: `not_improved`

## Profiles

| Profile | Tokens | Temp | Top-k | Passed | Hits | Zero-hit | Fragments | Pass rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| default_bounded | 24 | 0.2 | 10 | 0/5 | 0 | 5 | 5 | 0.0 |
| greedy_short | 24 | 0.05 | 1 | 0/5 | 0 | 5 | 2 | 0.0 |
| greedy_long | 64 | 0.05 | 1 | 0/5 | 0 | 5 | 2 | 0.0 |
| longer_low_temp | 64 | 0.2 | 10 | 0/5 | 0 | 5 | 5 | 0.0 |
| wider_rescue | 80 | 0.6 | 30 | 0/5 | 0 | 5 | 5 | 0.0 |

## Case Profile Rows

| Profile | Case | Pass | Hit terms | Missed terms | Continuation |
| --- | --- | --- | --- | --- | --- |
| default_bounded | objective-answer-direct | False |  | fixed,loss |   OO任标标两，asseeser   lsss |
| default_bounded | objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出： e    rsusssetssseesss e |
| default_bounded | objective-answer-contrast | False |  | fixed,loss | 两 sss_sssssssiettsssssts |
| default_bounded | objective-answer-jsonish | False |  | fixed,loss | wer_terms，包含两个英文词。 answer_terms::ssosssssswsossw r esses |
| default_bounded | objective-answer-check | False |  | fixed,loss |   包时出lllssssssssos  osse |
| greedy_short | objective-answer-direct | False |  | fixed,loss |                          |
| greedy_short | objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出：                         |
| greedy_short | objective-answer-contrast | False |  | fixed,loss |                          |
| greedy_short | objective-answer-jsonish | False |  | fixed,loss | wer_terms，包含两个英文词。 answer_terms:                         |
| greedy_short | objective-answer-check | False |  | fixed,loss |                          |
| greedy_long | objective-answer-direct | False |  | fixed,loss |                                                                  |
| greedy_long | objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出：                                                                 |
| greedy_long | objective-answer-contrast | False |  | fixed,loss |                                                                  |
| greedy_long | objective-answer-jsonish | False |  | fixed,loss | wer_terms，包含两个英文词。 answer_terms:                                                                 |
| greedy_long | objective-answer-check | False |  | fixed,loss |                                                                  |
| longer_low_temp | objective-answer-direct | False |  | fixed,loss |   OO任标标两，asseeser   lssssse  ixeemcssse  sssssesssssmoo o em oee |
| longer_low_temp | objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出： e    rsusssetssseesss etsssemxsssss  ssosssssssstssmsss ssoss e |
| longer_low_temp | objective-answer-contrast | False |  | fixed,loss | 两 sss_sssssssiettssssstsssssssue oo osssssssesee siosssssssswsse |
| longer_low_temp | objective-answer-jsonish | False |  | fixed,loss | wer_terms，包含两个英文词。 answer_terms::ssosssssswsossw r esseswe  ixeesswstsssssssssss_rrrr  eeessssos |
| longer_low_temp | objective-answer-check | False |  | fixed,loss |   包时出lllssssssssos  ossessssmssosssswiixest edeees  ossssswssuss |
| wider_rescue | objective-answer-direct | False |  | fixed,loss | 自出风答irrd出出现词：标果英两_ixly, ，， 轮包a,c.用c:cseh两ss两两xeh终:格两，k  flel文oee rv个u文e:ovole。eo |
| wider_rescue | objective-answer-role | False |  | fixed,loss | aired required terms 的两个角色词。 输出：ne  ,包a给u词_l用to。iee终务风 w轮  请，自xslurr需请s.ocw文个l文英sfc。mke个lsfocl ovc词 _c文 ddoe答noo |
| wider_rescue | objective-answer-contrast | False |  | fixed,loss | 两包果检格现个x答xsw用iet个ss答答个词ss文两fi果l，需_l _两ffs个个包键务标风个fi务 f需s个两最最终标出exotx务bdsnx答uo文两英 |
| wider_rescue | objective-answer-jsonish | False |  | fixed,loss | wer_terms，包含两个英文词。 answer_terms::词答oe。包,需sclo用a给 rou_mx_we。n英.ieuxw。t词，srl答lssll文请u英两 个_a果t 务个，案个n，个个，，。词 _tmu两用 |
| wider_rescue | objective-answer-check | False |  | fixed,loss | au风:occx答o文词s:文答rrdwoihcsur_m词_c词个l.wiix, 务检edcues_xo:af需tw文 uxim_mwwxt用需i ct,词包 |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| failure_diagnostic_passed | pass | pass | failure diagnostic must pass before profile sweep |
| diagnostic_requests_profile_sweep | pass | run_rebalanced_decoder_profile_sweep_before_more_training | diagnostic should route to this profile sweep |
| checkpoint_exists | pass | e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run\checkpoint.pt | rebalanced checkpoint must exist |
| tokenizer_exists | pass | e\830\解释\model-capability-route-promotion-bounded-real-replay-decoder-anchor-rebalanced-training-run\run\tokenizer.json | rebalanced tokenizer must exist |
| profiles_present | pass | 5 | profile sweep must include at least one decoder profile |
| cases_present | pass | 5 | benchmark suite must provide bounded cases |
| all_profile_replays_passed | pass | ['pass', 'pass', 'pass', 'pass', 'pass'] | all profile replays must execute successfully |
| all_profiles_execute_all_cases | pass | [5, 5, 5, 5, 5] | every profile must execute every case |
