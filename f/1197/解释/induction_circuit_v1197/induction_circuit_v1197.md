# MiniGPT induction circuit dissection v1197

- Generated: `2026-06-20T10:05:29Z`
- Status: `pass`
- Decision: `circuit_necessary_specific_composed_concentrated`

## Summary

| Metric | Value |
| --- | --- |
| status | pass |
| decision | circuit_necessary_specific_composed_concentrated |
| verdict | circuit_necessary_specific_composed_concentrated |
| K | 20 |
| T | 64 |
| width | 64 |
| n_head | 8 |
| seeds | 8 |
| base_acc | 0.9977 |
| unigram_acc | 0.1421 |
| chance | 0.05 |
| necessity | True |
| necessity_mean | True |
| necessity_zero | True |
| prev_ablate_acc | 0.162 |
| ind_ablate_acc | 0.1087 |
| prev_control_acc | 0.9724 |
| ind_control_acc | 0.98 |
| specificity | True |
| composition | True |
| comp_drop_prev | 0.7103 |
| comp_drop_nonprev_control | 0.0257 |
| prev_redundant | False |
| ind_redundant | True |
| prev_max_single_drop | 0.5204 |
| prev_class_drop | 0.8537 |
| ind_max_single_drop | 0.0863 |
| ind_class_drop | 0.8925 |
| usable_seed_frac | 0.714 |
| tau_grid_agree_frac | 1.0 |
| valid_measurement | True |
| flag_base_acc | 0.9977 |
| flag_unigram_acc | 0.1421 |
| flag_n_trained | 7 |
| flag_n_all | 8 |
| flag_n_comp_seeds | 7 |
| flag_usable_seed_frac | 0.714 |
| flag_classifiable_frac | 1.0 |
| flag_necessity | True |
| flag_necessity_mean | True |
| flag_necessity_zero | True |
| flag_prev_ablate_acc_mean | 0.162 |
| flag_ind_ablate_acc_mean | 0.1087 |
| flag_prev_ablate_acc_zero | 0.1609 |
| flag_ind_ablate_acc_zero | 0.1084 |
| flag_prev_control_acc | 0.9724 |
| flag_ind_control_acc | 0.98 |
| flag_specificity | True |
| flag_prev_redundant | False |
| flag_ind_redundant | True |
| flag_composition | True |
| flag_comp_drop_prev | 0.7103 |
| flag_comp_drop_nonprev_control | 0.0257 |
| flag_tau_grid_agree_frac | 1.0 |
| flag_prev_max_single_drop | 0.5204 |
| flag_ind_max_single_drop | 0.0863 |
| flag_prev_class_drop | 0.8537 |
| flag_ind_class_drop | 0.8925 |

## Rows

| arm | acc_mean | acc_zero | note |
| --- | --- | --- | --- |
| base (no ablation) | 0.9977 | 0.9977 | trained 2-layer model |
| ablate ALL prev-token heads | 0.162 | 0.1609 | necessity (L0) |
| ablate ALL induction heads | 0.1087 | 0.1084 | necessity (L1) |
| ablate matched-count control (L0 least-prev) | 0.9724 |  | specificity |
| ablate matched-count control (L1 least-ind) | 0.98 |  | specificity |

## Recommendations

- VERDICT (circuit_necessary_specific_composed_concentrated, status=pass): causal dissection of the induction circuit in a 2-layer width-64 MiniGPT (n_head=8) on v1196's clean induction task. Heads classified by attention pattern (prev-token mass i->i-1 in L0; induction mass i->most-recent-successor in L1). status='pass' certifies a VALID, non-degenerate, mean/zero-consistent, tau-robust measurement -- base model inducts 0.998 (>> unigram 0.142), >= 80% of seeds have >=2 heads per class.
- NECESSITY (MEAN-ablation primary; zero-ablation agreement required): ablating ALL prev-token heads -> acc 0.162, ALL induction heads -> 0.109 (both collapse toward unigram 0.142; two-part bar = absolute floor + relative drop>=50%). necessity=True (mean=True, zero=True; zero acc prev 0.161/ind 0.108). Mean-ablation preserves the LayerNorm operating point; zero is reported only as a consistency check.
- SPECIFICITY (count-matched): ablating the SAME NUMBER of L0 LEAST-prev heads -> acc 0.972 and L1 LEAST-induction heads -> 0.980 (vs the circuit-class collapse above). specificity=True -- it is the circuit heads specifically, not 'any k heads', that matter.
- REDUNDANCY (the honest nuance): max SINGLE-head drop prev 0.5204 / ind 0.0863 vs CLASS drop prev 0.8537 / ind 0.8925 -> prev_redundant=False, ind_redundant=True. Single-head ablation is compensated by the redundant copies; only removing the whole class breaks induction.
- COMPOSITION (prev-token -> induction, on a SEPARATE batch with controls): ablating prev-token heads drops the induction heads' attention by 0.710 vs only 0.026 for a matched non-prev L0 control -> composition=True (the induction heads READ the prev-token output; not a generic LayerNorm/residual shift). tau-robustness: verdict invariant in 100% of the threshold grid. SCOPE: 2-layer width-64 MiniGPT, n_head=8, K=20/T=64; the prev->induction circuit + depth requirement are textbook -- the NEW bit is the controlled multi-seed redundancy + matched-specificity + mean-ablation demonstration. NOT a claim about LLM induction heads.
