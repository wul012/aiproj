from __future__ import annotations

import ast
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, TypedDict

from minigpt.report_utils import (
    as_dict,
    csv_cell,
    html_escape,
    list_of_dicts,
    markdown_cell,
    utc_now,
    write_json_payload,
    write_output_bundle,
)

MAX_NAME_LENGTH = 40
DEFAULT_TARGETS = ("src", "scripts")
DEFAULT_BASELINE = Path("docs") / "elegance" / "name-baseline.json"


class NameItem(TypedDict):
    kind: str
    path: str
    qualname: str
    name: str
    length: int
    line: int
    digest: str


class ScanResult(TypedDict):
    items: list[NameItem]
    errors: list[dict[str, Any]]
    file_count: int


def scan_names(
    project_root: str | Path,
    *,
    targets: Iterable[str] = DEFAULT_TARGETS,
    max_length: int = MAX_NAME_LENGTH,
) -> ScanResult:
    root = Path(project_root).resolve()
    items: list[NameItem] = []
    errors: list[dict[str, Any]] = []
    files = _python_files(root, targets)
    for path in files:
        relative = path.relative_to(root).as_posix()
        if len(path.name) > max_length:
            items.append(_item("filename", relative, "", path.name, 0))
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=relative)
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append({"path": relative, "error": f"{type(exc).__name__}: {exc}"})
            continue
        items.extend(_public_names(tree, relative, max_length))
    return {
        "items": sorted(items, key=_item_key),
        "errors": errors,
        "file_count": len(files),
    }


def build_name_report(
    *,
    project_root: str | Path,
    baseline_path: str | Path = DEFAULT_BASELINE,
    targets: Iterable[str] = DEFAULT_TARGETS,
    update_baseline: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    target_list = list(targets)
    baseline = _inside_root(baseline_path, root)
    baseline_exists = baseline.is_file()
    payload, baseline_errors = _load_baseline(baseline, target_list)
    scan = scan_names(root, targets=target_list)
    items = scan["items"]
    current = {item["digest"] for item in items}
    old = set(payload.get("digests", [])) if payload else set()
    new_digests = current - old
    resolved = old - current
    first_adoption = update_baseline and not baseline_exists
    update_allowed = update_baseline and not baseline_errors and (first_adoption or not new_digests)
    new_items = [] if first_adoption else [item for item in items if item["digest"] in new_digests]
    blockers = list(baseline_errors) + [f"scan_error:{item['path']}" for item in scan["errors"]]
    if not baseline_exists and not update_baseline:
        blockers.append("baseline_missing")
    if update_baseline and not update_allowed:
        blockers.append("baseline_update_blocked")
    if new_items:
        blockers.append("new_name_violations")
    status = "pass" if not blockers else "fail"
    timestamp = generated_at or utc_now()
    kind_counts = dict(sorted(Counter(item["kind"] for item in items).items()))
    report = {
        "schema_version": 1,
        "title": "MiniGPT name budget gate",
        "generated_at": timestamp,
        "status": status,
        "decision": "continue_with_name_budget" if status == "pass" else "repair_name_budget",
        "baseline_path": baseline.relative_to(root).as_posix(),
        "targets": target_list,
        "summary": {
            "max_name_length": MAX_NAME_LENGTH,
            "scanned_file_count": scan["file_count"],
            "current_violation_count": len(items),
            "baseline_violation_count": len(old),
            "new_violation_count": len(new_items),
            "resolved_violation_count": len(resolved),
            "baseline_exists": baseline_exists,
            "baseline_update_requested": update_baseline,
            "baseline_update_allowed": update_allowed,
            "scan_error_count": len(scan["errors"]),
            "blocker_count": len(blockers),
        },
        "kind_counts": kind_counts,
        "blockers": blockers,
        "scan_errors": scan["errors"],
        "new_violations": new_items,
        "top_offenders": sorted(items, key=lambda item: (-item["length"], item["path"], item["name"]))[:25],
    }
    if update_allowed:
        write_name_baseline(
            baseline,
            targets=target_list,
            items=items,
            generated_at=timestamp,
        )
    return report


def write_name_baseline(
    path: str | Path,
    *,
    targets: list[str],
    items: list[NameItem],
    generated_at: str,
) -> None:
    payload = {
        "schema_version": 1,
        "policy": "aiproj_name_budget",
        "generated_at": generated_at,
        "max_name_length": MAX_NAME_LENGTH,
        "targets": targets,
        "violation_count": len(items),
        "kind_counts": dict(sorted(Counter(item["kind"] for item in items).items())),
        "digests": sorted(item["digest"] for item in items),
    }
    write_json_payload(payload, path)


def write_name_outputs(report: dict[str, Any], out_dir: str | Path) -> dict[str, str]:
    return write_output_bundle(
        out_dir,
        {
            "json": "name_budget.json",
            "csv": "name_budget.csv",
            "markdown": "name_budget.md",
            "html": "name_budget.html",
        },
        {
            "json": lambda path: write_json_payload(report, path),
            "csv": lambda path: _write_csv(report, path),
            "markdown": lambda path: _write_text(path, _markdown(report)),
            "html": lambda path: _write_text(path, _html(report)),
        },
    )


def _public_names(tree: ast.Module, path: str, max_length: int) -> list[NameItem]:
    items: list[NameItem] = []

    def visit(body: list[ast.stmt], scope: str) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                if _too_long(node.name, max_length):
                    items.append(_item(kind, path, scope, node.name, node.lineno))
                if isinstance(node, ast.ClassDef):
                    visit(node.body, _qualify(scope, node.name))
                continue
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                kind = "field" if scope else "variable"
                for name in _assigned_names(node):
                    if _too_long(name, max_length):
                        items.append(_item(kind, path, scope, name, node.lineno))

    visit(tree.body, "")
    return items


def _assigned_names(node: ast.Assign | ast.AnnAssign) -> list[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return [target.id for target in targets if isinstance(target, ast.Name)]


def _item(kind: str, path: str, scope: str, name: str, line: int) -> NameItem:
    qualname = _qualify(scope, name)
    key = json.dumps([kind, path, qualname, name], ensure_ascii=True, separators=(",", ":"))
    return {
        "kind": kind,
        "path": path,
        "qualname": qualname,
        "name": name,
        "length": len(name),
        "line": line,
        "digest": hashlib.sha256(key.encode("utf-8")).hexdigest(),
    }


def _load_baseline(path: Path, targets: list[str]) -> tuple[dict[str, Any], list[str]]:
    if not path.is_file():
        return {}, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {}, [f"baseline_unreadable:{type(exc).__name__}"]
    errors = []
    if not isinstance(payload, dict):
        return {}, ["baseline_not_object"]
    if payload.get("schema_version") != 1:
        errors.append("baseline_schema_invalid")
    if payload.get("policy") != "aiproj_name_budget":
        errors.append("baseline_policy_invalid")
    if payload.get("max_name_length") != MAX_NAME_LENGTH:
        errors.append("baseline_budget_invalid")
    if payload.get("targets") != targets:
        errors.append("baseline_targets_invalid")
    digests = payload.get("digests")
    if not isinstance(digests, list) or not all(isinstance(item, str) for item in digests):
        errors.append("baseline_digests_invalid")
    elif payload.get("violation_count") != len(digests) or len(set(digests)) != len(digests):
        errors.append("baseline_count_invalid")
    return (payload if not errors else {}), errors


def _python_files(root: Path, targets: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    for target in targets:
        base = _inside_root(target, root)
        candidates = [base] if base.is_file() else base.rglob("*.py") if base.is_dir() else []
        files.update(path for path in candidates if path.is_file() and path.suffix == ".py")
    return sorted(files)


def _inside_root(path: str | Path, root: Path) -> Path:
    candidate = Path(path)
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path must stay inside project root: {path}")
    return resolved


def _write_csv(report: dict[str, Any], path: Path) -> None:
    fields = ["state", "kind", "path", "qualname", "name", "length", "line", "digest"]
    rows = [("new", item) for item in list_of_dicts(report.get("new_violations"))]
    rows.extend(("top", item) for item in list_of_dicts(report.get("top_offenders")))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for state, item in rows:
            writer.writerow({field: csv_cell(state if field == "state" else item.get(field)) for field in fields})


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _markdown(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    lines = [
        "# MiniGPT Name Budget Gate",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Decision: `{report.get('decision')}`",
        f"- Baseline: `{report.get('baseline_path')}`",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        lines.append(f"| {markdown_cell(key)} | {markdown_cell(value)} |")
    lines.extend(["", "## Top offenders", "", "| Kind | Path | Name | Length |", "| --- | --- | --- | ---: |"])
    for item in list_of_dicts(report.get("top_offenders")):
        lines.append(
            "| " + " | ".join(markdown_cell(item.get(key)) for key in ("kind", "path", "name", "length")) + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _html(report: dict[str, Any]) -> str:
    summary = as_dict(report.get("summary"))
    status = html_escape(report.get("status"))
    decision = html_escape(report.get("decision"))
    baseline = html_escape(report.get("baseline_path"))
    cards = "".join(
        f"<div><small>{html_escape(key)}</small><strong>{html_escape(value)}</strong></div>"
        for key, value in summary.items()
    )
    rows = "".join(
        "<tr>"
        + "".join(f"<td>{html_escape(item.get(key))}</td>" for key in ("kind", "path", "name", "length"))
        + "</tr>"
        for item in list_of_dicts(report.get("top_offenders"))
    )
    return """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>MiniGPT name budget gate</title><style>body{{font-family:Arial,"Microsoft YaHei",sans-serif;background:#f5f7fa;color:#16202a;margin:0}}main{{max-width:1160px;margin:auto;padding:28px}}header,section{{background:#fff;border:1px solid #d5dce3;border-radius:8px;padding:18px;margin-bottom:14px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}}.cards div{{background:#eef3f7;padding:12px;border-radius:6px}}small,strong{{display:block}}strong{{font-size:20px;margin-top:5px}}table{{width:100%;border-collapse:collapse}}th,td{{border-bottom:1px solid #d5dce3;padding:8px;text-align:left;overflow-wrap:anywhere}}th:first-child,td:first-child{{min-width:72px}}th:last-child,td:last-child{{min-width:64px}}</style></head><body><main><header><h1>MiniGPT name budget gate</h1><p>Status: <strong>{status}</strong></p><p>Decision: <code>{decision}</code></p><p>Baseline: <code>{baseline}</code></p></header><section class="cards">{cards}</section><section><h2>Top offenders</h2><table><thead><tr><th>Kind</th><th>Path</th><th>Name</th><th>Length</th></tr></thead><tbody>{rows}</tbody></table></section></main></body></html>""".format(
        status=status, decision=decision, baseline=baseline, cards=cards, rows=rows
    )


def _too_long(name: str, max_length: int) -> bool:
    return not name.startswith("_") and len(name) > max_length


def _qualify(scope: str, name: str) -> str:
    return f"{scope}.{name}" if scope else name


def _item_key(item: NameItem) -> tuple[str, str, str]:
    return item["path"], item["kind"], item["qualname"]


def rebase_renamed_paths(
    old_items: list[NameItem],
    current_items: list[NameItem],
    baseline_digests: set[str],
) -> list[NameItem] | None:
    """v1295: prove a baseline path-rebase is rename-neutral, or refuse.

    File renames re-key baselined violations (the digest includes the path),
    so a pure rename shows up as N new + N resolved. The rebase is allowed
    ONLY when the multiset of (kind, qualname, length) of the new violations
    exactly equals that of the resolved ones — the violation stock is then
    provably unchanged modulo path and the ratchet cannot loosen through
    this door. Returns the item list to write as the rebased baseline, or
    None when neutrality cannot be proven (including when a resolved
    digest's metadata is absent from the old-tree scan).
    """
    current_digests = {item["digest"] for item in current_items}
    new_items = [item for item in current_items if item["digest"] not in baseline_digests]
    resolved_digests = baseline_digests - current_digests
    old_by_digest = {item["digest"]: item for item in old_items}
    if not new_items or len(new_items) != len(resolved_digests):
        return None
    if any(digest not in old_by_digest for digest in resolved_digests):
        return None
    resolved_items = [old_by_digest[digest] for digest in resolved_digests]

    def signature(item: NameItem) -> tuple[str, str, int]:
        return (item["kind"], item["qualname"], item["length"])

    if Counter(map(signature, new_items)) != Counter(map(signature, resolved_items)):
        return None
    return current_items
