# MiniGPT model capability route promotion release readiness summary contract check

- Status: `pass`
- Decision: `model_capability_route_promotion_release_readiness_summary_contract_check_passed`
- Ready: `True`
- Active routes: `objective_level_contrast`
- Boundary: `tiny_required_term_pair_probe_only`
- Claim: `seed_stable_pair_probe_route_accepted`
- Source digests: `3`

## Source Digests

| Kind | Exists | SHA-256 | Path |
| --- | --- | --- | --- |
| release_packet | True | 4b32d56640811e3dda52bba0e2f952227a6b9d7fb841ebaffa4ef301f4d82104 | e\795\解释\model-capability-route-promotion-release-packet\model_capability_route_promotion_release_packet.json |
| release_packet_review | True | 7259663a4798d7a7470aacc776d429346d4fb881c149d200141d995fa428164c | e\796\解释\model-capability-route-promotion-release-packet-review\model_capability_route_promotion_release_packet_review.json |
| governance_snapshot | True | f4be5170a62da02225816f8f7820f281e128928b23e89ccec85ca6aeed77e089 | e\800\解释\model-capability-route-promotion-governance-snapshot\model_capability_route_promotion_governance_snapshot.json |

## Checks

| Check | Status | Actual | Detail |
| --- | --- | --- | --- |
| summary_passed | pass | pass | release readiness summary must pass |
| summary_decision_ready | pass | model_capability_route_promotion_release_readiness_summary_ready | summary decision must be ready |
| summary_ready_flag | pass | True | summary ready flag must be true |
| summary_failed_count_zero | pass | 0 | summary failed_count must be zero |
| summary_issues_empty | pass | 0 | summary issues must be empty |
| summary_check_rows_clean | pass | {'pass': 15, 'fail': 0} | all summary check rows must pass |
| summary_check_counts_match | pass | {'summary': {'passed': 15, 'failed': 0}, 'actual': 15} | summary check counts must match check_rows |
| source_rows_present | pass | 3 | summary must record the three upstream source rows |
| source_kinds_match | pass | ['governance_snapshot', 'release_packet', 'release_packet_review'] | summary source kinds must match the expected packet/review/snapshot set |
| source_rows_mark_existing | pass | [{'kind': 'release_packet', 'path': 'e\\795\\解释\\model-capability-route-promotion-release-packet\\model_capability_route_promotion_release_packet.json', 'exists': True}, {'kind': 'release_packet_review', 'path': 'e\\796\\解释\\model-capability-route-promotion-release-packet-review\\model_capability_route_promotion_release_packet_review.json', 'exists': True}, {'kind': 'governance_snapshot', 'path': 'e\\800\\解释\\model-capability-route-promotion-governance-snapshot\\model_capability_route_promotion_governance_snapshot.json', 'exists': True}] | summary source rows must mark files as existing |
| source_files_digestible | pass | [{'kind': 'release_packet', 'path': 'e\\795\\解释\\model-capability-route-promotion-release-packet\\model_capability_route_promotion_release_packet.json', 'exists': True, 'sha256': '4b32d56640811e3dda52bba0e2f952227a6b9d7fb841ebaffa4ef301f4d82104'}, {'kind': 'release_packet_review', 'path': 'e\\796\\解释\\model-capability-route-promotion-release-packet-review\\model_capability_route_promotion_release_packet_review.json', 'exists': True, 'sha256': '7259663a4798d7a7470aacc776d429346d4fb881c149d200141d995fa428164c'}, {'kind': 'governance_snapshot', 'path': 'e\\800\\解释\\model-capability-route-promotion-governance-snapshot\\model_capability_route_promotion_governance_snapshot.json', 'exists': True, 'sha256': 'f4be5170a62da02225816f8f7820f281e128928b23e89ccec85ca6aeed77e089'}] | source files must exist and have digests |
| source_digest_kinds_match | pass | ['governance_snapshot', 'release_packet', 'release_packet_review'] | source digest rows must cover the expected source kinds |
| source_evidence_count_matches | pass | {'summary': 3, 'actual': 3} | evidence_count must match source rows |
| active_routes_align | pass | {'aligned': True, 'active_routes': ['objective_level_contrast'], 'route_count': 1, 'packet_routes': ['objective_level_contrast'], 'review_routes': ['objective_level_contrast'], 'snapshot_routes': ['objective_level_contrast']} | route alignment must be true |
| active_routes_match_summary | pass | {'summary': ['objective_level_contrast'], 'alignment': ['objective_level_contrast']} | summary routes must match route alignment |
| active_route_count_matches | pass | {'summary': 1, 'alignment': 1} | active route count must match route alignment |
| boundary_consistent | pass | ['tiny_required_term_pair_probe_only', 'tiny_required_term_pair_probe_only', 'tiny_required_term_pair_probe_only'] | boundary claim must be internally consistent |
| boundary_required | pass | {'summary': 'tiny_required_term_pair_probe_only', 'boundary_claim': 'tiny_required_term_pair_probe_only'} | boundary must remain tiny_required_term_pair_probe_only |
| claim_consistent | pass | ['seed_stable_pair_probe_route_accepted', 'seed_stable_pair_probe_route_accepted', 'seed_stable_pair_probe_route_accepted'] | model quality claim must be internally consistent |
| claim_bounded | pass | seed_stable_pair_probe_route_accepted | model quality claim must remain pair-probe scoped |
| claim_matches_summary | pass | {'summary': 'seed_stable_pair_probe_route_accepted', 'boundary_claim': 'seed_stable_pair_probe_route_accepted'} | summary claim must match boundary_claim |
| handoff_ready | pass | ready_for_bounded_governance_release | handoff status must be ready for bounded governance release |
| downstream_policy_allowed | pass | {'allowed': True, 'allowed_scope': 'bounded_route_promotion_release_governance_only', 'source_allowed_scope': 'bounded_model_capability_governance_only', 'route_ids': ['objective_level_contrast'], 'boundary': 'tiny_required_term_pair_probe_only', 'model_quality_claim': 'seed_stable_pair_probe_route_accepted', 'reason': 'packet, review, and governance snapshot agree inside the bounded route-promotion scope'} | downstream policy must allow bounded release governance |
| downstream_scope_bounded | pass | bounded_route_promotion_release_governance_only | downstream scope must be the release-readiness governance scope |
| source_downstream_scope_bounded | pass | bounded_model_capability_governance_only | source downstream scope must remain model-capability governance only |
