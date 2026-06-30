from __future__ import annotations

import unittest

from tests._bootstrap import ROOT

import minigpt.artifact_map as flat_artifact_map
import minigpt.dashboard as flat_dashboard
import minigpt.dashboard_render as flat_dashboard_render
import minigpt.dataset_card as flat_dataset_card
import minigpt.experiment_card as flat_experiment_card
import minigpt.governance as governance_package
import minigpt.governance.maturity as governance_maturity
import minigpt.governance.registry as governance_registry
import minigpt.governance.release as governance_release
import minigpt.manifest as flat_manifest
import minigpt.maturity as flat_maturity
import minigpt.maturity_narrative as flat_maturity_narrative
import minigpt.model_card as flat_model_card
import minigpt.model_report as flat_model_report
import minigpt.registry as flat_registry
import minigpt.release_bundle as flat_release_bundle
import minigpt.release_gate as flat_release_gate
import minigpt.release_gate_comparison as flat_release_gate_comparison
import minigpt.release_gate_policy as flat_release_gate_policy
import minigpt.release_readiness as flat_release_readiness
import minigpt.release_readiness_comparison as flat_release_readiness_comparison
import minigpt.release_readiness_drift_contract as flat_release_readiness_drift_contract
import minigpt.reports as reports_package
import minigpt.reports.artifact_map as reports_artifact_map
import minigpt.reports.cards as reports_cards
import minigpt.reports.dashboard as reports_dashboard
import minigpt.reports.manifest as reports_manifest
import minigpt.reports.model as reports_model
import minigpt.reports.utils as reports_utils
import minigpt.report_utils as flat_report_utils

REPORT_UTIL_EXPORTS = (
    "as_dict",
    "csv_cell",
    "html_escape",
    "list_of_dicts",
    "markdown_cell",
    "number_or_default",
    "string_list",
    "utc_now",
    "write_json_payload",
    "write_output_bundle",
)


class EvidencePackageReexportTests(unittest.TestCase):
    def test_reports_package_reexports_match_report_modules(self) -> None:
        self.assertIs(reports_package.ParameterGroup, flat_model_report.ParameterGroup)
        self.assertIs(reports_package.build_model_report, flat_model_report.build_model_report)
        self.assertIs(reports_package.write_model_report_svg, flat_model_report.write_model_report_svg)
        self.assertIs(reports_model.count_parameters, flat_model_report.count_parameters)
        self.assertIs(reports_model.parameter_groups, flat_model_report.parameter_groups)
        self.assertIs(reports_model.block_parameter_groups, flat_model_report.block_parameter_groups)
        self.assertIs(reports_model.tensor_shape_summary, flat_model_report.tensor_shape_summary)
        self.assertIs(reports_model.output_head_is_tied, flat_model_report.output_head_is_tied)

        self.assertIs(reports_package.build_dataset_card, flat_dataset_card.build_dataset_card)
        self.assertIs(reports_package.build_experiment_card, flat_experiment_card.build_experiment_card)
        self.assertIs(reports_package.build_model_card, flat_model_card.build_model_card)
        self.assertIs(reports_cards.build_dataset_card, flat_dataset_card.build_dataset_card)
        self.assertIs(reports_cards.build_experiment_card, flat_experiment_card.build_experiment_card)
        self.assertIs(reports_cards.build_model_card, flat_model_card.build_model_card)
        self.assertIs(reports_package.write_dataset_card_outputs, flat_dataset_card.write_dataset_card_outputs)
        self.assertIs(reports_package.write_experiment_card_outputs, flat_experiment_card.write_experiment_card_outputs)
        self.assertIs(reports_package.write_model_card_outputs, flat_model_card.write_model_card_outputs)
        self.assertIs(reports_cards.write_dataset_card_outputs, flat_dataset_card.write_dataset_card_outputs)
        self.assertIs(reports_cards.write_experiment_card_outputs, flat_experiment_card.write_experiment_card_outputs)
        self.assertIs(reports_cards.write_model_card_outputs, flat_model_card.write_model_card_outputs)

        self.assertIs(reports_package.DashboardArtifact, flat_dashboard.DashboardArtifact)
        self.assertIs(reports_package.collect_artifacts, flat_dashboard.collect_artifacts)
        self.assertIs(reports_package.build_dashboard_payload, flat_dashboard.build_dashboard_payload)
        self.assertIs(reports_package.write_dashboard, flat_dashboard.write_dashboard)
        self.assertIs(reports_package.render_dashboard_html, flat_dashboard_render.render_dashboard_html)
        self.assertIs(reports_dashboard.render_dashboard_html, flat_dashboard_render.render_dashboard_html)

        self.assertIs(reports_package.RUN_ARTIFACT_SPECS, flat_manifest.RUN_ARTIFACT_SPECS)
        self.assertIs(reports_package.build_run_manifest, flat_manifest.build_run_manifest)
        self.assertIs(reports_package.build_environment_metadata, flat_manifest.build_environment_metadata)
        self.assertIs(reports_package.collect_git_metadata, flat_manifest.collect_git_metadata)
        self.assertIs(reports_package.collect_run_artifacts, flat_manifest.collect_run_artifacts)
        self.assertIs(reports_package.sha256_file, flat_manifest.sha256_file)
        self.assertIs(reports_package.write_run_manifest_json, flat_manifest.write_run_manifest_json)
        self.assertIs(reports_package.write_run_manifest_svg, flat_manifest.write_run_manifest_svg)
        self.assertIs(reports_package.utc_now, flat_manifest.utc_now)
        self.assertIs(reports_manifest.build_run_manifest, flat_manifest.build_run_manifest)

        self.assertEqual(reports_package.DEFAULT_LIMIT, flat_artifact_map.DEFAULT_LIMIT)
        self.assertIs(reports_package.build_artifact_map_report, flat_artifact_map.build_artifact_map_report)
        self.assertIs(reports_package.write_artifact_map_outputs, flat_artifact_map.write_artifact_map_outputs)
        self.assertIs(reports_package.resolve_exit_code, flat_artifact_map.resolve_exit_code)
        self.assertIs(reports_artifact_map.resolve_exit_code, flat_artifact_map.resolve_exit_code)
        self.assertEqual(tuple(reports_utils.__all__), REPORT_UTIL_EXPORTS)
        self.assertIn("write_output_bundle", reports_package.__all__)
        for name in REPORT_UTIL_EXPORTS:
            with self.subTest(name=name):
                self.assertIs(getattr(reports_utils, name), getattr(flat_report_utils, name))
        self.assertIs(reports_package.write_output_bundle, reports_utils.write_output_bundle)

    def test_governance_package_reexports_match_governance_modules(self) -> None:
        self.assertIs(governance_package.build_release_bundle, flat_release_bundle.build_release_bundle)
        self.assertIs(governance_package.render_release_bundle_html, flat_release_bundle.render_release_bundle_html)
        self.assertIs(governance_package.write_release_bundle_outputs, flat_release_bundle.write_release_bundle_outputs)
        self.assertIs(governance_release.write_release_bundle_json, flat_release_bundle.write_release_bundle_json)

        self.assertIs(
            governance_package.DEFAULT_RELEASE_GATE_POLICY_PROFILE,
            flat_release_gate_policy.DEFAULT_RELEASE_GATE_POLICY_PROFILE,
        )
        self.assertIs(flat_release_gate.DEFAULT_RELEASE_GATE_POLICY_PROFILE, flat_release_gate_policy.DEFAULT_RELEASE_GATE_POLICY_PROFILE)
        self.assertIs(governance_package.RELEASE_GATE_POLICY_PROFILES, flat_release_gate_policy.RELEASE_GATE_POLICY_PROFILES)
        self.assertIs(flat_release_gate.RELEASE_GATE_POLICY_PROFILES, flat_release_gate_policy.RELEASE_GATE_POLICY_PROFILES)
        self.assertIs(governance_package.release_gate_policy_profiles, flat_release_gate_policy.release_gate_policy_profiles)
        self.assertIs(flat_release_gate.release_gate_policy_profiles, flat_release_gate_policy.release_gate_policy_profiles)
        self.assertIs(governance_package.resolve_release_gate_policy, flat_release_gate_policy.resolve_release_gate_policy)
        self.assertIs(flat_release_gate.resolve_release_gate_policy, flat_release_gate_policy.resolve_release_gate_policy)
        self.assertIs(governance_package.build_release_gate, flat_release_gate.build_release_gate)
        self.assertIs(governance_package.exit_code_for_gate, flat_release_gate.exit_code_for_gate)
        self.assertIs(governance_package.render_release_gate_html, flat_release_gate.render_release_gate_html)
        self.assertIs(governance_package.write_release_gate_outputs, flat_release_gate.write_release_gate_outputs)

        self.assertIs(governance_release.DEFAULT_COMPARISON_PROFILES, flat_release_gate_comparison.DEFAULT_COMPARISON_PROFILES)
        self.assertIs(
            governance_package.build_release_gate_profile_comparison,
            flat_release_gate_comparison.build_release_gate_profile_comparison,
        )
        self.assertIs(
            governance_release.write_release_gate_profile_comparison_outputs,
            flat_release_gate_comparison.write_release_gate_profile_comparison_outputs,
        )

        self.assertIs(
            governance_package.build_release_readiness_dashboard,
            flat_release_readiness.build_release_readiness_dashboard,
        )
        self.assertIs(governance_package.render_release_readiness_html, flat_release_readiness.render_release_readiness_html)
        self.assertIs(
            governance_package.write_release_readiness_outputs,
            flat_release_readiness.write_release_readiness_outputs,
        )
        self.assertIs(
            governance_package.build_release_readiness_comparison,
            flat_release_readiness_comparison.build_release_readiness_comparison,
        )
        self.assertIs(
            governance_package.render_release_readiness_comparison_html,
            flat_release_readiness_comparison.render_release_readiness_comparison_html,
        )
        self.assertIs(
            governance_package.write_release_readiness_comparison_outputs,
            flat_release_readiness_comparison.write_release_readiness_comparison_outputs,
        )
        self.assertIs(
            governance_package.resolve_release_readiness_comparison_path,
            flat_release_readiness_drift_contract.resolve_release_readiness_comparison_path,
        )
        self.assertIs(
            governance_package.check_release_readiness_drift_contract,
            flat_release_readiness_drift_contract.check_release_readiness_drift_contract,
        )
        self.assertIs(
            governance_release.write_release_readiness_drift_contract_outputs,
            flat_release_readiness_drift_contract.write_release_readiness_drift_contract_outputs,
        )

        self.assertIs(governance_package.CapabilitySpec, flat_maturity.CapabilitySpec)
        self.assertIs(governance_package.CAPABILITY_SPECS, flat_maturity.CAPABILITY_SPECS)
        self.assertIs(governance_package.build_maturity_summary, flat_maturity.build_maturity_summary)
        self.assertIs(governance_package.render_maturity_summary_html, flat_maturity.render_maturity_summary_html)
        self.assertIs(governance_package.write_maturity_summary_outputs, flat_maturity.write_maturity_summary_outputs)
        self.assertIs(governance_maturity.build_maturity_narrative, flat_maturity_narrative.build_maturity_narrative)
        self.assertIs(
            governance_package.render_maturity_narrative_html,
            flat_maturity_narrative.render_maturity_narrative_html,
        )
        self.assertIs(
            governance_package.write_maturity_narrative_outputs,
            flat_maturity_narrative.write_maturity_narrative_outputs,
        )

        self.assertIs(governance_package.REGISTRY_ARTIFACT_PATHS, flat_registry.REGISTRY_ARTIFACT_PATHS)
        self.assertIs(governance_package.RegisteredRun, flat_registry.RegisteredRun)
        self.assertIs(governance_package.build_run_registry, flat_registry.build_run_registry)
        self.assertIs(governance_package.discover_run_dirs, flat_registry.discover_run_dirs)
        self.assertIs(governance_package.summarize_registered_run, flat_registry.summarize_registered_run)
        self.assertIs(governance_package.render_registry_html, flat_registry.render_registry_html)
        self.assertIs(governance_package.write_registry_outputs, flat_registry.write_registry_outputs)
        self.assertIs(governance_registry.write_registry_json, flat_registry.write_registry_json)


if __name__ == "__main__":
    unittest.main()
