from __future__ import annotations

import unittest

from tests._bootstrap import ROOT

import minigpt
import minigpt.comparison as flat_comparison
import minigpt.core as core_package
import minigpt.core.dataset as core_dataset
import minigpt.core.history as core_history
import minigpt.core.model as core_model
import minigpt.core.rope as core_rope
import minigpt.core.tokenizer as core_tokenizer
import minigpt.data_prep as flat_data_prep
import minigpt.data_quality as flat_data_quality
import minigpt.dataset as flat_dataset
import minigpt.eval_suite as flat_eval_suite
import minigpt.eval_suite_design as flat_eval_suite_design
import minigpt.eval_suites as flat_eval_suites
import minigpt.evaluation as evaluation_package
import minigpt.evaluation.comparison as evaluation_comparison
import minigpt.evaluation.design as evaluation_design
import minigpt.evaluation.generation_quality as evaluation_generation_quality
import minigpt.evaluation.prediction as evaluation_prediction
import minigpt.evaluation.suite as evaluation_suite
import minigpt.evaluation.suites as evaluation_suites
import minigpt.generation_quality as flat_generation_quality
import minigpt.generation_profiles as flat_generation_profiles
import minigpt.history as flat_history
import minigpt.lm_training as flat_lm_training
import minigpt.model as flat_model
import minigpt.prediction as flat_prediction
import minigpt.rope as flat_rope
import minigpt.chat as flat_chat
import minigpt.script_runtime as flat_script_runtime
import minigpt.script_setup as flat_script_setup
import minigpt.server_checkpoints as flat_server_checkpoints
import minigpt.server_contracts as flat_server_contracts
import minigpt.server_generator as flat_server_generator
import minigpt.server_http as flat_server_http
import minigpt.server_logging as flat_server_logging
import minigpt.server_post_routes as flat_server_post_routes
import minigpt.server_request_history as flat_server_request_history
import minigpt.server_routes as flat_server_routes
import minigpt.serving as serving_package
import minigpt.serving.checkpoints as serving_checkpoints
import minigpt.serving.chat as serving_chat
import minigpt.serving.contracts as serving_contracts
import minigpt.serving.generator as serving_generator
import minigpt.serving.http as serving_http
import minigpt.serving.logging as serving_logging
import minigpt.serving.post_routes as serving_post_routes
import minigpt.serving.profiles as serving_profiles
import minigpt.serving.request_history as serving_request_history
import minigpt.serving.routes as serving_routes
import minigpt.serving.server as serving_server
import minigpt.tokenizer as flat_tokenizer
import minigpt.training as training_package
import minigpt.training.corpus_setup as training_corpus_setup
import minigpt.training.data_prep as training_data_prep
import minigpt.training.data_quality as training_data_quality
import minigpt.training.history as training_history
import minigpt.training.lm as training_lm
import minigpt.training.runtime as training_runtime


class FoundationPackageReexportTests(unittest.TestCase):
    def test_core_package_reexports_match_flat_core_modules(self) -> None:
        self.assertIs(core_package.GPTConfig, flat_model.GPTConfig)
        self.assertIs(core_package.MiniGPT, flat_model.MiniGPT)
        self.assertIs(core_package.TrainingRecord, flat_history.TrainingRecord)
        self.assertIs(core_package.load_tokenizer, flat_tokenizer.load_tokenizer)
        self.assertIs(core_model.GPTConfig, flat_model.GPTConfig)
        self.assertIs(core_model.MiniGPT, flat_model.MiniGPT)
        self.assertIs(core_tokenizer.CharTokenizer, flat_tokenizer.CharTokenizer)
        self.assertIs(core_tokenizer.BPETokenizer, flat_tokenizer.BPETokenizer)
        self.assertIs(core_tokenizer.load_tokenizer, flat_tokenizer.load_tokenizer)
        self.assertIs(core_dataset.load_text, flat_dataset.load_text)
        self.assertIs(core_dataset.split_token_ids, flat_dataset.split_token_ids)
        self.assertIs(core_dataset.get_batch, flat_dataset.get_batch)
        self.assertIs(core_history.TrainingRecord, flat_history.TrainingRecord)
        self.assertIs(core_history.append_record, flat_history.append_record)
        self.assertIs(core_history.load_records, flat_history.load_records)
        self.assertIs(core_history.summarize_records, flat_history.summarize_records)
        self.assertIs(core_history.write_loss_curve_svg, flat_history.write_loss_curve_svg)
        self.assertIs(core_rope.rotate_half, flat_rope.rotate_half)
        self.assertIs(core_rope.build_rope_cache, flat_rope.build_rope_cache)
        self.assertIs(core_rope.apply_rope, flat_rope.apply_rope)

    def test_evaluation_package_reexports_match_flat_evaluation_modules(self) -> None:
        self.assertIs(evaluation_package.PromptCase, flat_eval_suite.PromptCase)
        self.assertIs(evaluation_package.build_eval_suite_report, flat_eval_suite.build_eval_suite_report)
        self.assertIs(evaluation_package.standard_zh_prompt_suite, flat_eval_suites.standard_zh_prompt_suite)
        self.assertIs(evaluation_suite.PromptCase, flat_eval_suite.PromptCase)
        self.assertIs(evaluation_suite.build_eval_suite_report, flat_eval_suite.build_eval_suite_report)
        self.assertIs(evaluation_suites.standard_zh_prompt_suite, flat_eval_suites.standard_zh_prompt_suite)
        self.assertIs(evaluation_design.summarize_prompt_suite_design, flat_eval_suite_design.summarize_prompt_suite_design)
        self.assertIs(evaluation_comparison.RunComparison, flat_comparison.RunComparison)
        self.assertIs(evaluation_comparison.build_comparison_report, flat_comparison.build_comparison_report)
        self.assertIs(evaluation_comparison.write_comparison_outputs, flat_comparison.write_comparison_outputs)
        self.assertIs(evaluation_package.write_comparison_outputs, flat_comparison.write_comparison_outputs)
        self.assertIs(
            evaluation_generation_quality.build_generation_quality_report,
            flat_generation_quality.build_generation_quality_report,
        )
        self.assertIs(
            evaluation_generation_quality.write_generation_quality_outputs,
            flat_generation_quality.write_generation_quality_outputs,
        )
        self.assertIs(
            evaluation_package.write_generation_quality_outputs,
            flat_generation_quality.write_generation_quality_outputs,
        )
        self.assertIs(evaluation_package.TokenPrediction, flat_prediction.TokenPrediction)
        self.assertIs(evaluation_prediction.top_k_predictions, flat_prediction.top_k_predictions)
        self.assertIs(evaluation_prediction.perplexity_from_loss, flat_prediction.perplexity_from_loss)
        self.assertIs(evaluation_prediction.write_predictions_svg, flat_prediction.write_predictions_svg)
        self.assertIs(evaluation_package.top_k_predictions, flat_prediction.top_k_predictions)
        self.assertIs(evaluation_package.perplexity_from_loss, flat_prediction.perplexity_from_loss)

    def test_serving_package_reexports_match_server_modules(self) -> None:
        self.assertIs(serving_package.GenerationRequest, flat_server_contracts.GenerationRequest)
        self.assertIs(serving_package.MiniGPTGenerator, flat_server_generator.MiniGPTGenerator)
        self.assertIs(serving_contracts.GenerationRequest, flat_server_contracts.GenerationRequest)
        self.assertIs(serving_contracts.parse_generation_request, minigpt.server.parse_generation_request)
        self.assertIs(serving_generator.MiniGPTGenerator, flat_server_generator.MiniGPTGenerator)
        self.assertIs(serving_checkpoints.discover_checkpoint_options, flat_server_checkpoints.discover_checkpoint_options)
        self.assertIs(serving_routes.handle_get_request, flat_server_routes.handle_get_request)
        self.assertIs(serving_post_routes.handle_post_request, flat_server_post_routes.handle_post_request)
        self.assertIs(serving_http.send_json, flat_server_http.send_json)
        self.assertIs(serving_logging.build_generation_log_event, flat_server_logging.build_generation_log_event)
        self.assertIs(
            serving_request_history.handle_request_history_endpoint,
            flat_server_request_history.handle_request_history_endpoint,
        )
        self.assertIs(serving_server.run_server, minigpt.server.run_server)
        self.assertIs(serving_package.run_server, minigpt.server.run_server)
        self.assertIs(serving_chat.ChatTurn, flat_chat.ChatTurn)
        self.assertIs(serving_chat.build_chat_prompt, flat_chat.build_chat_prompt)
        self.assertIs(serving_chat.prepare_chat_prompt, flat_chat.prepare_chat_prompt)
        self.assertIs(serving_chat.assistant_reply_from_generation, flat_chat.assistant_reply_from_generation)
        self.assertIs(serving_package.ChatTurn, flat_chat.ChatTurn)
        self.assertIs(serving_package.build_chat_prompt, flat_chat.build_chat_prompt)
        self.assertIs(serving_profiles.GenerationProfile, flat_generation_profiles.GenerationProfile)
        self.assertIs(serving_profiles.generation_profile_ids, flat_generation_profiles.generation_profile_ids)
        self.assertIs(serving_package.GenerationProfile, flat_generation_profiles.GenerationProfile)
        self.assertIs(serving_package.generation_profile_ids, flat_generation_profiles.generation_profile_ids)

    def test_training_package_reexports_match_training_modules(self) -> None:
        self.assertIs(training_package.PreparedDataset, flat_data_prep.PreparedDataset)
        self.assertIs(training_package.TrainingRecord, flat_history.TrainingRecord)
        self.assertIs(training_package.build_prepared_dataset, flat_data_prep.build_prepared_dataset)
        self.assertIs(training_package.train_lm, flat_lm_training.train_lm)
        self.assertIs(training_data_prep.PreparedDataset, flat_data_prep.PreparedDataset)
        self.assertIs(training_data_prep.discover_text_files, flat_data_prep.discover_text_files)
        self.assertIs(training_data_prep.normalize_text, flat_data_prep.normalize_text)
        self.assertIs(training_data_prep.build_prepared_dataset, flat_data_prep.build_prepared_dataset)
        self.assertIs(training_data_prep.build_dataset_report, flat_data_prep.build_dataset_report)
        self.assertIs(training_data_quality.DatasetQualityIssue, flat_data_quality.DatasetQualityIssue)
        self.assertIs(training_data_quality.build_dataset_quality_report, flat_data_quality.build_dataset_quality_report)
        self.assertIs(training_history.TrainingRecord, flat_history.TrainingRecord)
        self.assertIs(training_lm.train_lm, flat_lm_training.train_lm)
        self.assertIs(training_runtime.choose_device, flat_script_runtime.choose_device)
        self.assertIs(training_runtime.seed_everything, flat_script_runtime.seed_everything)
        self.assertIs(training_corpus_setup.setup_single_corpus, flat_script_setup.setup_single_corpus)


if __name__ == "__main__":
    unittest.main()
