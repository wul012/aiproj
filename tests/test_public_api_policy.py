from __future__ import annotations

import unittest

from tests._bootstrap import ROOT

import minigpt
from minigpt._root_exports import ROOT_FACADE_ALL_EXPORTS, ROOT_FACADE_LAZY_EXPORTS
import minigpt.chat as flat_chat
import minigpt.comparison as flat_comparison
import minigpt.data_prep as flat_data_prep
import minigpt.dataset as flat_dataset
import minigpt.eval_suite as flat_eval_suite
import minigpt.eval_suites as flat_eval_suites
import minigpt.generation_profiles as flat_generation_profiles
import minigpt.history as flat_history
import minigpt.model as flat_model
import minigpt.model_report as flat_model_report
import minigpt.prediction as flat_prediction
import minigpt.server_contracts as flat_server_contracts
import minigpt.server_generator as flat_server_generator
import minigpt.tokenizer as flat_tokenizer
from minigpt.core.dataset import get_batch, load_text, split_token_ids
from minigpt.core.model import GPTConfig, MiniGPT
from minigpt.core.tokenizer import BPETokenizer, CharTokenizer, load_tokenizer
from minigpt.evaluation.comparison import build_comparison_report
from minigpt.evaluation.prediction import TokenPrediction, perplexity_from_loss, top_k_predictions, write_predictions_svg
from minigpt.evaluation.suite import (
    PromptCase,
    PromptSuite,
    build_eval_suite_report,
    build_prompt_result,
    load_builtin_prompt_suite,
    load_prompt_suite,
)
from minigpt.evaluation.suites import standard_zh_prompt_suite
from minigpt.reports.model import build_model_report
from minigpt.reports.utils import write_output_bundle
from minigpt.serving.contracts import (
    CheckpointOption,
    GenerationRequest,
    GenerationResponse,
    GenerationStreamChunk,
    InferenceSafetyProfile,
)
from minigpt.serving.generator import MiniGPTGenerator
from minigpt.serving.chat import ChatTurn, build_chat_prompt, prepare_chat_prompt
from minigpt.serving.profiles import GenerationProfile, generation_profile_ids
from minigpt.training.data_prep import (
    PreparedDataset,
    SourceFileSummary,
    build_prepared_dataset,
    write_prepared_dataset,
)
from minigpt.training.history import (
    TrainingRecord,
    append_record,
    load_records,
    summarize_records,
    write_loss_curve_svg,
)

ROOT_FACADE_ALL_EXPORT_BUDGET = 288
ROOT_FACADE_LAZY_EXPORT_BUDGET = 318
ROOT_FACADE_ENTRYPOINT_LINE_BUDGET = 80
ROOT_FACADE_TABLE_MODULE_LINE_BUDGET = 500


class PublicApiPolicyTests(unittest.TestCase):
    def test_tier_1_owner_package_imports_are_available(self) -> None:
        stable_objects = [
            GPTConfig,
            MiniGPT,
            CharTokenizer,
            BPETokenizer,
            load_tokenizer,
            load_text,
            split_token_ids,
            get_batch,
            PreparedDataset,
            SourceFileSummary,
            build_prepared_dataset,
            write_prepared_dataset,
            TrainingRecord,
            append_record,
            load_records,
            summarize_records,
            write_loss_curve_svg,
            PromptCase,
            PromptSuite,
            build_eval_suite_report,
            build_prompt_result,
            load_builtin_prompt_suite,
            load_prompt_suite,
            standard_zh_prompt_suite,
            TokenPrediction,
            top_k_predictions,
            perplexity_from_loss,
            write_predictions_svg,
            GenerationRequest,
            GenerationResponse,
            GenerationStreamChunk,
            CheckpointOption,
            InferenceSafetyProfile,
            MiniGPTGenerator,
            ChatTurn,
            build_chat_prompt,
            prepare_chat_prompt,
            GenerationProfile,
            generation_profile_ids,
            build_model_report,
            build_comparison_report,
            write_output_bundle,
        ]

        self.assertTrue(all(obj is not None for obj in stable_objects))

    def test_flat_module_imports_remain_compatibility_aliases(self) -> None:
        self.assertIs(GPTConfig, flat_model.GPTConfig)
        self.assertIs(MiniGPT, flat_model.MiniGPT)
        self.assertIs(CharTokenizer, flat_tokenizer.CharTokenizer)
        self.assertIs(BPETokenizer, flat_tokenizer.BPETokenizer)
        self.assertIs(load_tokenizer, flat_tokenizer.load_tokenizer)
        self.assertIs(load_text, flat_dataset.load_text)
        self.assertIs(split_token_ids, flat_dataset.split_token_ids)
        self.assertIs(get_batch, flat_dataset.get_batch)
        self.assertIs(PreparedDataset, flat_data_prep.PreparedDataset)
        self.assertIs(SourceFileSummary, flat_data_prep.SourceFileSummary)
        self.assertIs(build_prepared_dataset, flat_data_prep.build_prepared_dataset)
        self.assertIs(write_prepared_dataset, flat_data_prep.write_prepared_dataset)
        self.assertIs(TrainingRecord, flat_history.TrainingRecord)
        self.assertIs(append_record, flat_history.append_record)
        self.assertIs(load_records, flat_history.load_records)
        self.assertIs(summarize_records, flat_history.summarize_records)
        self.assertIs(write_loss_curve_svg, flat_history.write_loss_curve_svg)
        self.assertIs(PromptCase, flat_eval_suite.PromptCase)
        self.assertIs(PromptSuite, flat_eval_suite.PromptSuite)
        self.assertIs(build_eval_suite_report, flat_eval_suite.build_eval_suite_report)
        self.assertIs(build_prompt_result, flat_eval_suite.build_prompt_result)
        self.assertIs(load_builtin_prompt_suite, flat_eval_suite.load_builtin_prompt_suite)
        self.assertIs(load_prompt_suite, flat_eval_suite.load_prompt_suite)
        self.assertIs(standard_zh_prompt_suite, flat_eval_suites.standard_zh_prompt_suite)
        self.assertIs(perplexity_from_loss, flat_prediction.perplexity_from_loss)
        self.assertIs(top_k_predictions, flat_prediction.top_k_predictions)
        self.assertIs(write_predictions_svg, flat_prediction.write_predictions_svg)
        self.assertIs(GenerationRequest, flat_server_contracts.GenerationRequest)
        self.assertIs(GenerationResponse, flat_server_contracts.GenerationResponse)
        self.assertIs(GenerationStreamChunk, flat_server_contracts.GenerationStreamChunk)
        self.assertIs(CheckpointOption, flat_server_contracts.CheckpointOption)
        self.assertIs(InferenceSafetyProfile, flat_server_contracts.InferenceSafetyProfile)
        self.assertIs(MiniGPTGenerator, flat_server_generator.MiniGPTGenerator)
        self.assertIs(ChatTurn, flat_chat.ChatTurn)
        self.assertIs(build_chat_prompt, flat_chat.build_chat_prompt)
        self.assertIs(GenerationProfile, flat_generation_profiles.GenerationProfile)
        self.assertIs(generation_profile_ids, flat_generation_profiles.generation_profile_ids)
        self.assertIs(build_model_report, flat_model_report.build_model_report)
        self.assertIs(build_comparison_report, flat_comparison.build_comparison_report)

    def test_core_facade_keeps_key_compatibility_exports(self) -> None:
        self.assertIs(minigpt.GPTConfig, GPTConfig)
        self.assertIs(minigpt.MiniGPT, MiniGPT)
        self.assertIs(minigpt.CharTokenizer, CharTokenizer)
        self.assertIs(minigpt.BPETokenizer, BPETokenizer)
        self.assertIs(minigpt.load_tokenizer, load_tokenizer)
        self.assertIs(minigpt.TrainingRecord, TrainingRecord)
        self.assertIs(minigpt.PromptCase, PromptCase)
        self.assertIs(minigpt.PromptSuite, PromptSuite)
        self.assertIs(minigpt.build_eval_suite_report, build_eval_suite_report)
        self.assertIs(minigpt.standard_zh_prompt_suite, standard_zh_prompt_suite)

    def test_server_facade_keeps_contract_compatibility_exports(self) -> None:
        self.assertIs(minigpt.GenerationRequest, minigpt.server.GenerationRequest)
        self.assertIs(minigpt.GenerationResponse, minigpt.server.GenerationResponse)
        self.assertIs(minigpt.CheckpointOption, minigpt.server.CheckpointOption)
        self.assertIs(minigpt.InferenceSafetyProfile, minigpt.server.InferenceSafetyProfile)
        self.assertIs(minigpt.parse_generation_request, minigpt.server.parse_generation_request)

    def test_root_facade_export_budget_does_not_grow(self) -> None:
        all_names, exports = _root_facade_tables()
        public_api_policy = (ROOT / "docs" / "public-api.md").read_text(encoding="utf-8")
        entrypoint_lines = (ROOT / "src" / "minigpt" / "__init__.py").read_text(encoding="utf-8").splitlines()
        table_modules = sorted((ROOT / "src" / "minigpt").glob("_root*exports*.py"))

        self.assertLessEqual(len(all_names), ROOT_FACADE_ALL_EXPORT_BUDGET)
        self.assertLessEqual(len(exports), ROOT_FACADE_LAZY_EXPORT_BUDGET)
        self.assertLessEqual(len(entrypoint_lines), ROOT_FACADE_ENTRYPOINT_LINE_BUDGET)
        for module_path in table_modules:
            with self.subTest(module=module_path.name):
                line_count = len(module_path.read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(line_count, ROOT_FACADE_TABLE_MODULE_LINE_BUDGET)
        self.assertEqual(len(all_names), len(set(all_names)))
        self.assertEqual(set(), set(all_names) - set(exports))
        self.assertIn("Root Facade Export Budget", public_api_policy)


def _root_facade_tables() -> tuple[list[str], dict[str, tuple[str, str]]]:
    return list(ROOT_FACADE_ALL_EXPORTS), dict(ROOT_FACADE_LAZY_EXPORTS)


if __name__ == "__main__":
    unittest.main()
