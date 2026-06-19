# MiniGPT continual learning / catastrophic forgetting v1193

- Generated: `2026-06-19T09:22:39Z`
- Status: `pass`
- Decision: `catastrophic_forgetting_mitigated_by_replay`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | catastrophic_forgetting_mitigated_by_replay |
| verdict | catastrophic_forgetting_mitigated_by_replay |
| task_a | add |
| task_b | mul |
| p | 23 |
| chance | 0.04348 |
| b_majority_prior | 0.0898 |
| leak_free | True |
| seeds | 3 |
| train_frac | 0.8 |
| b_budget | 1500 |
| accA_plateau | 0.9843 |
| naive_accA_after_B | 0.0409 |
| naive_forgetting | 0.9434 |
| naive_forgetting_std | 0.0 |
| naive_accB_after_B | 0.805 |
| continue_on_A_forgetting | -0.0063 |
| random_label_B_forgetting | 0.9371 |
| wrong_replay_forgetting | 0.9308 |
| replay_max_buffer | 128 |
| replay_max_forgetting | 0.0377 |
| joint_accA | 0.8616 |
| joint_accB | 0.8365 |
| savings_recovered_k |  |
| valid_measurement | True |
| flag_g_a_consolidated | True |
| flag_g_b_learned | True |
| flag_g_jointly_learnable | True |
| flag_g_no_operand_leak | True |
| flag_g_floor_clean | True |
| flag_forgets | True |
| flag_catastrophic | True |
| flag_replay_reduces_forgetting | True |
| flag_wrong_replay_reduces | False |
| flag_replay_specific | True |
| flag_replay_dose_response_monotone | True |
| flag_forgetting_is_task_structure_specific | False |
| flag_forgetting_is_distribution_shift_not_structure | True |
| flag_savings_fast_masking | False |

## Rows

| arm | acc_A | acc_A_std | forgetting | note |
| --- | --- | --- | --- | --- |
| consolidated_A | 0.9843 | 0.0054 | 0.0 | plateau (A learned) |
| naive_sequential | 0.0409 | 0.0054 | 0.9434 | after B; acc_B=0.805 |
| continue_on_A | 0.9906 | 0.0 | -0.0063 | floor (no shift) |
| random_label_B | 0.0472 | 0.0 | 0.9371 | null: structure vs drift |
| wrong_replay_B | 0.0535 | 0.0 | 0.9308 | replay B not A (must still forget) |
| multitask_joint | 0.8616 | 0.095 | 0.0 | upper bound; acc_B=0.836 |
| replay_buffer_0 | 0.0409 | 0.0 | 0.9434 | = naive floor |
| replay_buffer_8 | 0.6226 | 0.0945 | 0.3616 | A-train replay |
| replay_buffer_32 | 0.9214 | 0.0357 | 0.0629 | A-train replay |
| replay_buffer_128 | 0.9465 | 0.025 | 0.0377 | A-train replay |

## Recommendations

- VERDICT (catastrophic_forgetting_mitigated_by_replay): task A=(add) consolidated to test acc 0.984; after training task B=(mul) for 1500 steps A collapses to 0.041 (chance 0.043) -> FORGETTING 0.943±0.000. status='pass' certifies a VALID measurement (A consolidated to a plateau, B genuinely learned 0.805 >> majority-prior 0.090, jointly learnable, no operand leak), NOT a flattering result. 'catastrophic'=True is gated on the drop reaching near chance.
- FLOOR & TRAJECTORY: continue-on-A (no distribution shift) forgets only -0.006 (g_floor_clean=True) — so forgetting needs a NEW distribution, not just more steps. acc_A through the B phase: [0.1761, 0.04088, 0.04088, 0.04088, 0.04717, 0.04717, 0.05975, 0.04717, 0.05031, 0.04088, 0.04403, 0.04717, 0.04717, 0.04088, 0.04088] — collapse is sharp/instant.
- REPLAY (mitigation): replaying A-train examples during B reduces forgetting as a dose-response buf=0:0.943, buf=8:0.362, buf=32:0.063, buf=128:0.038 (monotone=True); replay reduces forgetting=True. SPECIFIC (not 'any extra gradients'): WRONG-replay (replaying B, not A) still forgets 0.931 (wrong_replay_reduces=False, replay_specific=True). Replay works by RE-EXPOSING A data — it is data, not magic (the v1173 discipline).
- HONEST MECHANISM: random-label-B (same B inputs, SHUFFLED targets) forgets 0.937 vs real-B 0.943 — task-structure-specific=False. They forget about equally, so the forgetting is DISTRIBUTION-SHIFT-driven (training on a new input distribution overwrites the shared weights), NOT specific to B-task structure — reported honestly.
- SAVINGS (erasure vs masking): relearning A reaches its plateau only beyond the probed budget (slow => closer to ERASURE). JOINT upper bound (no forgetting by construction): acc_A 0.862, acc_B 0.836. SCOPE: toy modular-arithmetic generalization on a 1-layer transformer; NOT a claim about instruction-tuned LLM forgetting.
