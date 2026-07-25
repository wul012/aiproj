from __future__ import annotations

import csv
from datetime import datetime, timezone
import html
import json
from pathlib import Path
from typing import Any, Callable, Iterable
from hashlib import sha256
import hashlib
import re


CI_ARCHIVED_PATH_PORTABILITY_CHECK_READY_REGRESSION_REASON = "archived_path_portability_check_not_ready"
CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON = "boundary_gate_plan_check_not_ready"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def write_json_payload(payload: Any, path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_output_bundle(
    out_dir: str | Path,
    filenames: dict[str, str],
    writers: dict[str, Callable[[Path], None]],
) -> dict[str, str]:
    filename_keys = set(filenames)
    writer_keys = set(writers)
    if filename_keys != writer_keys:
        missing_writers = sorted(filename_keys - writer_keys)
        missing_filenames = sorted(writer_keys - filename_keys)
        details = []
        if missing_writers:
            details.append("missing writers: " + ", ".join(missing_writers))
        if missing_filenames:
            details.append("missing filenames: " + ", ".join(missing_filenames))
        raise ValueError("output bundle keys must match" + (f" ({'; '.join(details)})" if details else ""))

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {key: root / filename for key, filename in filenames.items()}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for key, writer in writers.items():
        writer(paths[key])
    return {key: str(value) for key, value in paths.items()}


def locate_upstream_report(path: str | Path, default_name: str) -> Path:
    source = Path(path)
    if source.is_dir():
        return source / default_name
    return source


def read_json_object(path: str | Path, *, description: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{description} must be a JSON object")
    return dict(payload)


def read_json_object_or_empty(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    source = Path(path)
    if not source.is_file():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    return dict(payload) if isinstance(payload, dict) else {}


def write_csv_row(row: dict[str, Any], path: str | Path, fieldnames: list[str]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({field: csv_cell(row.get(field)) for field in fieldnames})


def csv_cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def make_artifact_row(
    key: str, path: str | Path, *, exists: bool | None = None, count: int | None = None
) -> dict[str, Any]:
    item_path = Path(path)
    present = item_path.exists() if exists is None else bool(exists)
    resolved_count = (1 if present else 0) if count is None else int(count)
    return {"key": str(key), "path": str(item_path), "exists": present, "count": resolved_count}


def make_artifact_rows(items: Iterable[tuple[str, str | Path]]) -> list[dict[str, Any]]:
    return [make_artifact_row(key, path) for key, path in items]


def archived_reference_path(value: Any) -> Path:
    """Resolve archived artifact refs written on Windows or POSIX runners."""
    return Path(str(value).replace("\\", "/"))


def resolve_archived_reference_path(value: Any, base_dir: str | Path | None = None) -> Path | None:
    if not value:
        return None
    candidate = archived_reference_path(value)
    if candidate.is_file() or candidate.is_absolute() or base_dir is None:
        return candidate
    base = Path(base_dir)
    for anchor in (base, *base.parents):
        based = anchor / candidate
        if based.is_file():
            return based
    return candidate


def count_available_artifacts(rows: Iterable[dict[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("exists"))


def as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def positive_int_mapping(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, raw_count in value.items():
        name = str(key).strip()
        count = int(number_or_default(raw_count, 0, int))
        if name and count > 0:
            result[name] = count
    return dict(sorted(result.items()))


def ci_regression_reason_count(reason: str, *values: Any) -> int:
    reason_name = str(reason).strip()
    if not reason_name:
        return 0
    for value in values:
        count = positive_int_mapping(value).get(reason_name)
        if count is not None:
            return count
    return 0


def ci_boundary_plan_check_ready_regression_count(*values: Any) -> int:
    for value in values:
        count = _int_count_or_none(value)
        if count is not None:
            return max(0, count)
    return ci_regression_reason_count(CI_BOUNDARY_PLAN_CHECK_READY_REGRESSION_REASON, *values)


def format_mapping(value: Any) -> str:
    counts = as_dict(value)
    if not counts:
        return "none"
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts))


def list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def list_of_strs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def number_or_none(value: Any, number_type: type[int] | type[float] = float) -> int | float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return number_type(value)
    except (TypeError, ValueError):
        return None


def number_or_default(
    value: Any, default: int | float = 0, number_type: type[int] | type[float] = float
) -> int | float:
    number = number_or_none(value, number_type)
    return default if number is None else number


def display_command(value: Any) -> str:
    if not isinstance(value, list):
        return "" if value is None else str(value)
    return " ".join(_quote_command_part(str(part)) for part in value)


def markdown_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _quote_command_part(part: str) -> str:
    if not part:
        return '""'
    if any(char.isspace() for char in part) or '"' in part:
        return '"' + part.replace('"', '\\"') + '"'
    return part


def _int_count_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or isinstance(value, (dict, list, tuple)) or value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def html_card(label: str, value: Any) -> str:
    """The span/strong summary card used by the governance HTML reports."""
    return f"<div class=\"card\"><span>{html_escape(label)}</span><strong>{html_escape(value)}</strong></div>"

def html_card_label_value(label: str, value: Any) -> str:
    """The label-div/strong card variant."""
    return f'<div class="card"><div class="label">{html_escape(label)}</div><strong>{html_escape(value)}</strong></div>'

def html_check_row(row: dict[str, Any]) -> str:
    """One ``<tr>`` for the id/status/actual/detail check table."""
    return "<tr>" + "".join(f"<td>{html_escape(row.get(key))}</td>" for key in ["id", "status", "actual", "detail"]) + "</tr>"

def html_term(label: str, value: Any) -> str:
    """One ``<dt>/<dd>`` pair for definition-list report sections."""
    return f"<dt>{html_escape(label)}</dt><dd>{html_escape(value)}</dd>"

def path_exists(path: str | Path | None) -> bool:
    """True iff ``path`` is truthy and exists on disk."""
    return bool(path) and Path(str(path)).exists()


def format_value(value: Any) -> str:
    if value is None:
        return 'missing'
    if isinstance(value, float):
        return f'{value:.5g}'
    return str(value)


def as_dict_or_empty(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def html_e(value: Any) -> str:
    return html.escape('' if value is None else str(value), quote=True)


def as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def csv_clean(value: Any) -> Any:
    cell = csv_cell(value)
    return cell.rstrip() if isinstance(cell, str) else cell


def score_fraction(expected_terms: list[str], continuation: str) -> dict[str, Any]:
    lowered = continuation.lower()
    hit_terms = [term for term in expected_terms if term.lower() in lowered]
    missed_terms = [term for term in expected_terms if term not in hit_terms]
    return {'hit_terms': hit_terms, 'missed_terms': missed_terms, 'case_pass': bool(expected_terms) and (not missed_terms)}


def join_terms(value: Any) -> str:
    if not isinstance(value, list):
        return ''
    return ','.join((str(item) for item in value))


def artifact_entries(root: Path) -> list[dict[str, Any]]:
    rows = []
    for key, name in [('checkpoint', 'checkpoint.pt'), ('tokenizer', 'tokenizer.json'), ('metrics', 'metrics.jsonl'), ('train_config', 'train_config.json'), ('run_manifest', 'run_manifest.json'), ('sample', 'sample.txt'), ('prepared_corpus', 'prepared_corpus.txt')]:
        path = root / name
        rows.append({'key': key, 'path': str(path), 'exists': path.is_file(), 'size': path.stat().st_size if path.is_file() else 0})
    return rows


def html_receipt_row(row: dict[str, Any]) -> str:
    return '<tr>' + ''.join((f'<td>{html_escape(row.get(key))}</td>' for key in ['consumer_name', 'lookup_key', 'publication_id', 'granted_use', 'blocked_uses', 'promotion_ready', 'receipt_status'])) + '</tr>'


def write_jsonl(report: dict[str, Any], path: Path) -> None:
    rows = [json.dumps(row, ensure_ascii=False) for row in list_of_dicts(report.get('patch_examples'))]
    path.write_text('\n'.join(rows) + ('\n' if rows else ''), encoding='utf-8')


def as_optional_float(value: Any) -> float | None:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def rank_label(value: Any) -> str:
    if value is None or value == '':
        return 'unranked'
    return f'#{int(value)}'


def sha256_file(path: str | Path | None) -> str:
    if not path or not Path(str(path)).is_file():
        return ''
    return sha256(Path(str(path)).read_bytes()).hexdigest()


def as_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def base_dir(source_path: str | Path | None, search_base: str | Path | None) -> Path:
    if search_base is not None:
        return Path(search_base)
    if source_path is not None:
        return Path(source_path).parent
    return Path.cwd()


def fmt_any(value: Any) -> str:
    if isinstance(value, float):
        return f'{value:.5g}'
    return 'missing' if value is None else str(value)


def fmt_mapping(value: Any) -> str:
    if not isinstance(value, dict) or not value:
        return 'missing'
    return ', '.join((f'{key}:{value[key]}' for key in sorted(value)))


def locate(path: str | Path, filename: str) -> Path:
    source = Path(path)
    if source.is_file():
        return source
    nested = source / filename
    if nested.is_file():
        return nested
    raise FileNotFoundError(f'cannot locate {filename} under {source}')


def cases_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    suite = as_dict(report.get('benchmark_suite'))
    return {str(item.get('case_id')): item for item in list_of_dicts(suite.get('cases'))}


def cause(cause_id: str, detail: str) -> dict[str, str]:
    return {'id': cause_id, 'detail': detail}


def cause_row(row: dict[str, Any]) -> str:
    return f"<tr><td>{html_escape(row.get('cause_id'))}</td><td>{html_escape(row.get('severity'))}</td><td>{html_escape(row.get('evidence'))}</td><td>{html_escape(row.get('detail'))}</td></tr>"


def entry_row(row: dict[str, Any]) -> str:
    return f"<tr><td>{html_escape(row.get('lookup_key'))}</td><td>{html_escape(row.get('entry_id'))}</td><td>{html_escape(row.get('registry_status'))}</td><td>{html_escape(row.get('bounded_publication_accepted'))}</td><td>{html_escape(row.get('promotion_ready'))}</td><td>{html_escape(row.get('consumer_boundary'))}</td><td>{html_escape(row.get('model_quality_claim'))}</td></tr>"


def fmt_int(value: Any) -> str:
    if value is None:
        return 'missing'
    return f'{int(value):,}'


def fmt_signed(value: Any) -> str:
    if value is None:
        return 'missing'
    number = float(value)
    return f'{number:+.5g}'


def preview(value: Any, limit: int=90) -> str:
    text = str(value or '').replace('\n', '\\n').replace('\t', '\\t')
    return text if len(text) <= limit else text[:limit - 1] + '...'


def probe_html(row: dict[str, Any]) -> str:
    return f"<li>{html_escape(row.get('id'))}: {html_escape(row.get('prompt'))} -> {html_escape(row.get('expected_term'))}</li>"


def relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return list_of_dicts(report.get('rows'))


def sha256_or_empty(path: str | Path | None) -> str:
    if not path:
        return ''
    source = Path(path)
    if not source.is_file():
        return ''
    digest = hashlib.sha256()
    with source.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def unique_strings(values: Any) -> list[str]:
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in items:
            items.append(text)
    return items


def best_routes(branch_rows: list[dict[str, Any]]) -> list[str]:
    best = max([int(row.get('hit_term_count') or 0) for row in branch_rows] or [0])
    return [str(row.get('source_label') or '') for row in branch_rows if int(row.get('hit_term_count') or 0) == best]


def case_by_id(rows: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    for row in rows:
        if row.get('case_id') == case_id:
            return row
    return {}


def contains_count(rows: list[str], needle: str) -> int:
    return sum((1 for row in rows if needle in row))


def count_by(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value or 'unknown')
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def counts(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def evidence_html(row: dict[str, Any]) -> str:
    return f"<tr><td>{html_escape(row.get('label'))}</td><td>{html_escape(row.get('status'))}</td><td>{html_escape(row.get('decision'))}</td><td>{html_escape(row.get('key_result'))}</td></tr>"


def evidence_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ['| Label | Status | Decision | Key result |', '| --- | --- | --- | --- |']
    for row in list_of_dicts(report.get('evidence_rows')):
        rows.append('| ' + ' | '.join([markdown_cell(row.get('label')), markdown_cell(row.get('status')), markdown_cell(row.get('decision')), markdown_cell(row.get('key_result'))]) + ' |')
    return rows


def family_html(row: dict[str, Any]) -> str:
    return f"<tr><td>{html_escape(row.get('family'))}</td><td>{html_escape(row.get('role'))}</td><td>{html_escape(row.get('target_term'))}</td><td>{html_escape(len(row.get('rows', [])))}</td></tr>"


def fmt_delta(value: Any) -> str:
    if value is None or value == '':
        return 'missing'
    return f'{float(value):+.5g}'


def generation_html(row: dict[str, Any]) -> str:
    return f"<tr><td>{html_escape(row.get('case'))}</td><td>{html_escape(row.get('term'))}</td><td>{html_escape(row.get('scaffold_prompt'))}</td><td>{html_escape(row.get('generated_hit_count'))}</td><td>{html_escape(row.get('continuation_hit_count'))}</td><td>{html_escape(row.get('continuation_preview'))}</td></tr>"


def int_if_whole(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def join(value: Any) -> str:
    if not isinstance(value, list):
        return ''
    return ','.join((str(item) for item in value))


def packet_row(row: dict[str, Any]) -> str:
    return '<tr>' + ''.join((f'<td>{html_escape(row.get(key))}</td>' for key in ['packet_id', 'consumer_name', 'lookup_key', 'publication_id', 'granted_use', 'promotion_ready', 'receipt_status', 'packet_status'])) + '</tr>'


def packet_rows(packet: dict[str, Any], consumer_receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{'packet_id': packet.get('packet_id'), 'consumer_name': packet.get('consumer_name'), 'lookup_key': row.get('lookup_key'), 'publication_id': row.get('publication_id'), 'granted_use': packet.get('granted_use'), 'blocked_uses': packet.get('blocked_uses'), 'promotion_ready': False, 'receipt_status': row.get('receipt_status'), 'packet_status': packet.get('packet_status')} for row in consumer_receipts]


def reason_drift_status(added: list[str], removed: list[str]) -> str:
    if added and removed:
        return 'mixed'
    if added:
        return 'regressed'
    if removed:
        return 'recovered'
    return 'stable'


def route_html(row: dict[str, Any]) -> str:
    pair_full = f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"
    return f"<tr><td>{html_escape(row.get('source_label'))}</td><td>{html_escape(row.get('route_type'))}</td><td>{html_escape(pair_full)}</td><td>{html_escape(','.join((str(term) for term in row.get('hit_terms', []))))}</td><td>{html_escape(','.join((str(reason) for reason in row.get('rejection_reasons', []))))}</td></tr>"


def route_markdown_rows(report: dict[str, Any]) -> list[str]:
    rows = ['| Route | Type | Pair-full | Hit terms | Reasons |', '| --- | --- | ---: | --- | --- |']
    for row in list_of_dicts(report.get('route_rows')):
        rows.append('| ' + ' | '.join([markdown_cell(row.get('source_label')), markdown_cell(row.get('route_type')), markdown_cell(f"{row.get('pair_full_seed_count')}/{row.get('seed_count')}"), markdown_cell(','.join((str(term) for term in row.get('hit_terms', [])))), markdown_cell(','.join((str(reason) for reason in row.get('rejection_reasons', []))))]) + ' |')
    return rows


def slug(value: str) -> str:
    slug = re.sub('[^a-zA-Z0-9]+', '-', value.strip().lower()).strip('-')
    return slug or 'term'


def target_prompt_hits(prompts: list[dict[str, Any]]) -> list[str]:
    hits = []
    for row in prompts:
        prompt = str(row.get('prompt') or '').lower()
        terms = [str(term).lower() for term in row.get('expected_terms', ['fixed', 'loss'])]
        if any((term and term in prompt for term in terms)):
            hits.append(str(row.get('case_id') or row.get('prompt') or 'unknown'))
    return hits


def term_count(text: str, terms: list[str]) -> dict[str, int]:
    lowered = text.lower()
    return {term: lowered.count(term.lower()) for term in terms}


def unique_sorted(value: Any) -> list[str]:
    return sorted({str(item) for item in string_list(value) if str(item)})
