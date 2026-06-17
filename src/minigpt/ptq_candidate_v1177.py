from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from minigpt.readability_report_artifacts import write_readability_outputs
from minigpt.report_utils import as_dict, list_of_dicts, locate_upstream_report, number_or_default, read_json_object, utc_now

PTQ_CANDIDATE_STEM = "ptq_candidate_v1177"
PTQ_SOURCE_DEFAULT_NAME = "ptq_v1175.json"


@dataclass(frozen=True)
class PtqCandidatePolicy:
    max_dce_nats: float = 0.08
    max_exact_match_drop: float = 0.10
    max_kl_nats: float = 0.10

    def as_dict(self) -> dict[str, float]:
        return {
            "max_dce_nats": self.max_dce_nats,
            "max_exact_match_drop": self.max_exact_match_drop,
            "max_kl_nats": self.max_kl_nats,
        }


def locate_ptq_report(path: str | Path) -> Path:
    return locate_upstream_report(path, PTQ_SOURCE_DEFAULT_NAME)


def read_json_report(path: str | Path) -> dict[str, Any]:
    return read_json_object(path, description="PTQ source report")


def build_ptq_candidate_report(
    ptq_report_or_path: dict[str, Any] | str | Path,
    *,
    policy: PtqCandidatePolicy | None = None,
    source_ptq_report: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_path: Path | None = None
    if isinstance(ptq_report_or_path, (str, Path)):
        source_path = locate_ptq_report(ptq_report_or_path)
        ptq_report = read_json_report(source_path)
    else:
        ptq_report = dict(ptq_report_or_path)
        if source_ptq_report is not None:
            source_path = locate_ptq_report(source_ptq_report)

    resolved_policy = policy or PtqCandidatePolicy()
    summary = as_dict(ptq_report.get("summary"))
    fp32_ce = number_or_default(summary.get("fp32_ce"), 0.0)
    fp32_em = number_or_default(summary.get("fp32_exact_match"), 0.0)
    source_status = str(ptq_report.get("status", "unknown"))
    source_decision = str(ptq_report.get("decision", "unknown"))
    source_verdict = str(summary.get("verdict", "unknown"))

    rows = [_candidate_row(row, fp32_ce=fp32_ce, fp32_em=fp32_em, policy=resolved_policy) for row in _s1_rows(ptq_report)]
    viable = [row for row in rows if row["quality_budget_pass"]]
    viable.sort(key=lambda row: (row["eff_bits"], row["ce_mean"], row["granularity"], row["bits"]))
    selected = viable[0] if viable else None
    for rank, row in enumerate(viable, start=1):
        row["viable_rank"] = rank

    source_ok = source_status == "pass"
    candidate_ready = source_ok and selected is not None
    status = "pass" if candidate_ready else ("review" if source_ok else "fail")
    decision = "ptq_deployment_candidate_selected" if candidate_ready else (
        "tighten_or_rerun_ptq_candidate_policy" if source_ok else "repair_source_ptq_report"
    )
    selected_summary = _selected_summary(selected)

    return {
        "schema_version": 1,
        "title": "MiniGPT PTQ deployment candidate selector v1177",
        "generated_at": generated_at or utc_now(),
        "status": status,
        "decision": decision,
        "summary": {
            "candidate_ready": candidate_ready,
            "source_status": source_status,
            "source_decision": source_decision,
            "source_verdict": source_verdict,
            "source_ptq_report": str(source_path) if source_path is not None else "",
            "policy": resolved_policy.as_dict(),
            "fp32_ce": round(float(fp32_ce), 6),
            "fp32_exact_match": round(float(fp32_em), 6),
            "candidate_count": len(rows),
            "viable_candidate_count": len(viable),
            "selected_candidate_id": selected_summary.get("candidate_id"),
            "selected_granularity": selected_summary.get("granularity"),
            "selected_bits": selected_summary.get("bits"),
            "selected_eff_bits": selected_summary.get("eff_bits"),
            "selected_ce_mean": selected_summary.get("ce_mean"),
            "selected_dce_mean": selected_summary.get("dce_mean"),
            "selected_kl_mean": selected_summary.get("kl_mean"),
            "selected_em_mean": selected_summary.get("em_mean"),
            "selected_em_drop": selected_summary.get("em_drop"),
            "selected_effective_bit_reduction_vs_fp32": _reduction(selected_summary.get("eff_bits")),
            "boundary": "quality_cost_selection_only_no_int_kernel_speed_or_memory_claim",
            "next_step": "measure_selected_ptq_candidate_with_real_runtime_or_keep_as_quality_cost_reference",
        },
        "rows": rows,
        "selected_candidate": selected_summary,
        "rejected_candidates": [row for row in rows if not row["quality_budget_pass"]],
        "recommendations": _recommendations(selected, resolved_policy, source_status, source_verdict),
        "csv_fieldnames": [
            "candidate_id",
            "granularity",
            "bits",
            "eff_bits",
            "ce_mean",
            "dce_mean",
            "kl_mean",
            "em_mean",
            "em_drop",
            "quality_budget_pass",
            "reject_reasons",
            "viable_rank",
        ],
    }


def write_ptq_candidate_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_readability_outputs(report, out_dir, stem=PTQ_CANDIDATE_STEM, row_title="PTQ Candidate Rows")


def resolve_exit_code(report: dict[str, Any], *, require_pass: bool = False) -> int:
    if require_pass and report.get("status") != "pass":
        return 1
    return 0


def _s1_rows(ptq_report: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in list_of_dicts(ptq_report.get("rows"))
        if row.get("sweep") == "S1" and row.get("component") == "all"
    ]


def _candidate_row(row: dict[str, Any], *, fp32_ce: float, fp32_em: float, policy: PtqCandidatePolicy) -> dict[str, Any]:
    granularity = str(row.get("granularity", "unknown"))
    bits = int(number_or_default(row.get("bits"), 0, int))
    eff_bits = float(number_or_default(row.get("eff_bits"), bits))
    ce_mean = float(number_or_default(row.get("ce_mean"), 0.0))
    dce_mean = float(number_or_default(row.get("dce_mean"), ce_mean - fp32_ce))
    kl_mean = float(number_or_default(row.get("kl_mean"), 0.0))
    em_mean = float(number_or_default(row.get("em_mean"), 0.0))
    em_drop = max(0.0, float(fp32_em) - em_mean)
    reject_reasons = _reject_reasons(dce_mean=dce_mean, em_drop=em_drop, kl_mean=kl_mean, policy=policy)
    return {
        "candidate_id": f"{granularity}:{bits}b",
        "granularity": granularity,
        "bits": bits,
        "eff_bits": round(eff_bits, 6),
        "ce_mean": round(ce_mean, 6),
        "dce_mean": round(dce_mean, 6),
        "kl_mean": round(kl_mean, 6),
        "em_mean": round(em_mean, 6),
        "em_drop": round(em_drop, 6),
        "quality_budget_pass": not reject_reasons,
        "reject_reasons": ",".join(reject_reasons),
        "viable_rank": "",
    }


def _reject_reasons(*, dce_mean: float, em_drop: float, kl_mean: float, policy: PtqCandidatePolicy) -> list[str]:
    reasons: list[str] = []
    if dce_mean > policy.max_dce_nats:
        reasons.append("dce_above_budget")
    if em_drop > policy.max_exact_match_drop:
        reasons.append("exact_match_drop_above_budget")
    if kl_mean > policy.max_kl_nats:
        reasons.append("kl_above_budget")
    return reasons


def _selected_summary(selected: dict[str, Any] | None) -> dict[str, Any]:
    if selected is None:
        return {}
    return {
        key: selected.get(key)
        for key in (
            "candidate_id",
            "granularity",
            "bits",
            "eff_bits",
            "ce_mean",
            "dce_mean",
            "kl_mean",
            "em_mean",
            "em_drop",
            "viable_rank",
        )
    }


def _reduction(eff_bits: Any) -> float | None:
    if eff_bits is None:
        return None
    return round(1.0 - float(eff_bits) / 32.0, 6)


def _recommendations(selected: dict[str, Any] | None, policy: PtqCandidatePolicy, source_status: str, source_verdict: str) -> list[str]:
    if source_status != "pass":
        return [
            f"Source PTQ report is {source_status}; do not select a deployment candidate until the source measurement passes.",
            "This selector consumes v1175 quality-cost evidence only. It cannot repair a failed or incomplete PTQ sweep.",
        ]
    if selected is None:
        return [
            "No candidate fits the configured quality budget. Loosen policy only with an explicit product tolerance, or rerun PTQ with more schemes.",
            f"Current budget: dCE<={policy.max_dce_nats}, EM drop<={policy.max_exact_match_drop}, KL<={policy.max_kl_nats}.",
        ]
    return [
        f"Selected {selected['candidate_id']} as the lowest effective-bits candidate inside the configured quality budget.",
        f"Keep the v1175 verdict in view ({source_verdict}): this is a quality-cost candidate, not proof of runtime speed or memory savings.",
        "Before deployment, validate the selected scheme with a real quantized runtime kernel or keep it as an offline compression-quality reference.",
    ]


__all__ = [
    "PTQ_CANDIDATE_STEM",
    "PTQ_SOURCE_DEFAULT_NAME",
    "PtqCandidatePolicy",
    "build_ptq_candidate_report",
    "locate_ptq_report",
    "read_json_report",
    "resolve_exit_code",
    "write_ptq_candidate_outputs",
]
