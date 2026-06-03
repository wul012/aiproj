# MiniGPT model capability route promotion decision index contract check

- Status: `pass`
- Decision: `model_capability_route_promotion_decision_index_contract_check_passed`
- Ready: `True`
- Source decisions: `1`
- Original routes: `['objective_level_contrast']`
- Rebuilt routes: `['objective_level_contrast']`

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| source_paths_present | pass | 1 | decision index must record source decision paths |
| status | pass | {'source': 'pass', 'rebuilt': 'pass'} | status must match when rebuilt from source decisions |
| decision | pass | {'source': 'model_capability_route_promotion_decision_index_ready', 'rebuilt': 'model_capability_route_promotion_decision_index_ready'} | decision must match when rebuilt from source decisions |
| failed_count | pass | {'source': 0, 'rebuilt': 0} | failed_count must match when rebuilt from source decisions |
| decision_index_ready | pass | {'source': True, 'rebuilt': True} | decision_index_ready must match when rebuilt from source decisions |
| accepted_route_count | pass | {'source': 1, 'rebuilt': 1} | accepted_route_count must match when rebuilt from source decisions |
| route_ids | pass | {'source': ['objective_level_contrast'], 'rebuilt': ['objective_level_contrast']} | route_ids must match when rebuilt from source decisions |
| boundary | pass | {'source': 'tiny_required_term_pair_probe_only', 'rebuilt': 'tiny_required_term_pair_probe_only'} | boundary must match when rebuilt from source decisions |
| model_quality_claim | pass | {'source': 'seed_stable_pair_probe_route_accepted', 'rebuilt': 'seed_stable_pair_probe_route_accepted'} | model_quality_claim must match when rebuilt from source decisions |
| entries | pass | {'source': [{'route_id': 'objective_level_contrast', 'entry_status': 'accepted', 'review_scope': 'bounded_route_promotion_review_only', 'boundary': 'tiny_required_term_pair_probe_only', 'model_quality_claim': 'seed_stable_pair_probe_route_accepted'}], 'rebuilt': [{'route_id': 'objective_level_contrast', 'entry_status': 'accepted', 'review_scope': 'bounded_route_promotion_review_only', 'boundary': 'tiny_required_term_pair_probe_only', 'model_quality_claim': 'seed_stable_pair_probe_route_accepted'}]} | entries must match when rebuilt from source decisions |
