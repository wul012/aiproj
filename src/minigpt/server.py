from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import partial
import html as html_lib
import json
import mimetypes
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Iterator
from urllib.parse import parse_qs, unquote, urlparse

from .playground import write_playground


@dataclass(frozen=True)
class InferenceSafetyProfile:
    max_prompt_chars: int = 2000
    max_new_tokens: int = 512
    min_temperature: float = 0.05
    max_temperature: float = 2.0
    max_top_k: int = 200
    max_body_bytes: int = 16 * 1024

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CheckpointOption:
    id: str
    name: str
    path: str
    exists: bool
    is_default: bool
    tokenizer_path: str | None
    tokenizer_exists: bool
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int | None
    checkpoint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationPairRequest:
    left: GenerationRequest
    right: GenerationRequest

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
        }


@dataclass(frozen=True)
class GenerationResponse:
    prompt: str
    generated: str
    continuation: str
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int | None
    checkpoint: str
    tokenizer: str
    checkpoint_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationStreamChunk:
    index: int
    token_id: int | None
    text: str
    generated: str
    continuation: str
    checkpoint: str
    tokenizer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MiniGPTGenerator:
    def __init__(
        self,
        checkpoint_path: str | Path,
        tokenizer_path: str | Path | None = None,
        device: str = "auto",
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.tokenizer_path = Path(tokenizer_path) if tokenizer_path is not None else self.checkpoint_path.parent / "tokenizer.json"
        self.device_name = device
        self._loaded: tuple[Any, Any, Any] | None = None

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        torch, model, tokenizer = self._load()
        prompt_ids = tokenizer.encode(request.prompt)
        if not prompt_ids:
            raise ValueError("prompt produced no token ids")
        if len(prompt_ids) > model.config.block_size:
            prompt_ids = prompt_ids[-model.config.block_size :]
        if request.seed is not None:
            torch.manual_seed(request.seed)
            if self._device(torch).type == "cuda":
                torch.cuda.manual_seed_all(request.seed)

        idx = torch.tensor([prompt_ids], dtype=torch.long, device=self._device(torch))
        with torch.no_grad():
            out = model.generate(
                idx,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_k=request.top_k,
            )
        generated = tokenizer.decode(out[0].tolist())
        continuation = generated[len(request.prompt) :] if generated.startswith(request.prompt) else generated
        return GenerationResponse(
            prompt=request.prompt,
            generated=generated,
            continuation=continuation,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_k=request.top_k,
            seed=request.seed,
            checkpoint=str(self.checkpoint_path),
            tokenizer=getattr(tokenizer, "name", "unknown"),
        )

    def stream(self, request: GenerationRequest) -> Iterator[GenerationStreamChunk]:
        torch, model, tokenizer = self._load()
        prompt_ids = tokenizer.encode(request.prompt)
        if not prompt_ids:
            raise ValueError("prompt produced no token ids")
        if len(prompt_ids) > model.config.block_size:
            prompt_ids = prompt_ids[-model.config.block_size :]
        if request.seed is not None:
            torch.manual_seed(request.seed)
            if self._device(torch).type == "cuda":
                torch.cuda.manual_seed_all(request.seed)

        idx = torch.tensor([prompt_ids], dtype=torch.long, device=self._device(torch))
        for index in range(request.max_new_tokens):
            next_idx = model.sample_next(idx, temperature=request.temperature, top_k=request.top_k)
            idx = torch.cat((idx, next_idx), dim=1)
            token_id = int(next_idx[0, 0].item())
            generated = tokenizer.decode(idx[0].tolist())
            continuation = generated[len(request.prompt) :] if generated.startswith(request.prompt) else generated
            yield GenerationStreamChunk(
                index=index,
                token_id=token_id,
                text=tokenizer.decode([token_id]),
                generated=generated,
                continuation=continuation,
                checkpoint=str(self.checkpoint_path),
                tokenizer=getattr(tokenizer, "name", "unknown"),
            )

    def _load(self) -> tuple[Any, Any, Any]:
        if self._loaded is not None:
            return self._loaded

        import torch

        from .model import GPTConfig, MiniGPT
        from .tokenizer import load_tokenizer

        device = self._device(torch)
        checkpoint = torch.load(self.checkpoint_path, map_location=device, weights_only=False)
        tokenizer = load_tokenizer(self.tokenizer_path)
        config = GPTConfig(**checkpoint["config"])
        model = MiniGPT(config).to(device)
        model.load_state_dict(checkpoint["model"])
        model.eval()
        self._loaded = (torch, model, tokenizer)
        return self._loaded

    def _device(self, torch: Any) -> Any:
        if self.device_name == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.device_name == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
        return torch.device(self.device_name)


def parse_generation_request(
    payload: dict[str, Any],
    safety_profile: InferenceSafetyProfile | None = None,
) -> GenerationRequest:
    safety = safety_profile or InferenceSafetyProfile()
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        raise ValueError("prompt cannot be empty")
    if len(prompt) > safety.max_prompt_chars:
        raise ValueError(f"prompt must be at most {safety.max_prompt_chars} characters")
    max_new_tokens = _as_int(payload.get("max_new_tokens", 80), "max_new_tokens")
    if max_new_tokens < 1 or max_new_tokens > safety.max_new_tokens:
        raise ValueError(f"max_new_tokens must be between 1 and {safety.max_new_tokens}")
    temperature = _as_float(payload.get("temperature", 0.8), "temperature")
    if temperature < safety.min_temperature or temperature > safety.max_temperature:
        raise ValueError(f"temperature must be between {safety.min_temperature:g} and {safety.max_temperature:g}")
    top_k_raw = payload.get("top_k", 30)
    top_k = None if _empty_top_k(top_k_raw) else _as_int(top_k_raw, "top_k")
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be at least 1 when provided")
    if top_k is not None and top_k > safety.max_top_k:
        raise ValueError(f"top_k must be at most {safety.max_top_k}")
    seed_raw = payload.get("seed")
    seed = None if seed_raw in {None, ""} else _as_int(seed_raw, "seed")
    checkpoint_raw = payload.get("checkpoint")
    checkpoint = None if checkpoint_raw in {None, ""} else str(checkpoint_raw).strip()
    if checkpoint == "":
        checkpoint = None
    return GenerationRequest(
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        seed=seed,
        checkpoint=checkpoint,
    )


def parse_generation_pair_request(
    payload: dict[str, Any],
    safety_profile: InferenceSafetyProfile | None = None,
) -> GenerationPairRequest:
    left_selector = payload.get("left_checkpoint", payload.get("checkpoint"))
    right_selector = payload.get("right_checkpoint")
    if right_selector in {None, ""}:
        raise ValueError("right_checkpoint is required")
    left_payload = dict(payload)
    right_payload = dict(payload)
    left_payload["checkpoint"] = left_selector
    right_payload["checkpoint"] = right_selector
    return GenerationPairRequest(
        left=parse_generation_request(left_payload, safety_profile),
        right=parse_generation_request(right_payload, safety_profile),
    )


def build_health_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    *,
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    request_log = Path(request_log_path) if request_log_path is not None else root / "inference_requests.jsonl"
    safety = safety_profile or InferenceSafetyProfile()
    checkpoints = discover_checkpoint_options(root, checkpoint, checkpoint_candidates=checkpoint_candidates)
    return {
        "status": "ok",
        "run_dir": str(root),
        "checkpoint": str(checkpoint),
        "checkpoint_exists": checkpoint.exists(),
        "tokenizer_exists": (root / "tokenizer.json").exists(),
        "playground_exists": (root / "playground.html").exists(),
        "sample_lab_exists": (root / "sample_lab" / "sample_lab.json").exists(),
        "model_info_endpoint": "/api/model-info",
        "generate_endpoint": "/api/generate",
        "generate_stream_endpoint": "/api/generate-stream",
        "generate_pair_endpoint": "/api/generate-pair",
        "generate_pair_artifact_endpoint": "/api/generate-pair-artifact",
        "checkpoints_endpoint": "/api/checkpoints",
        "checkpoint_compare_endpoint": "/api/checkpoint-compare",
        "checkpoint_count": len(checkpoints),
        "default_checkpoint_id": checkpoints[0].id if checkpoints else None,
        "safety": safety.to_dict(),
        "request_log": str(request_log),
        "request_log_exists": request_log.exists(),
    }


def build_model_info_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    checkpoint_id: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    tokenizer = Path(tokenizer_path) if tokenizer_path is not None else root / "tokenizer.json"
    manifest = _read_json(root / "run_manifest.json")
    train_config = _read_json(root / "train_config.json")
    model_report = _read_json(root / "model_report" / "model_report.json")
    dataset_version = _read_json(root / "dataset_version.json")
    model = _pick_dict(manifest, "model")
    training = _pick_dict(manifest, "training")
    data = _pick_dict(manifest, "data")
    report_config = _pick_dict(model_report, "config")
    config = _pick_dict(model, "config") or report_config
    version_summary = _pick_dict(data, "dataset_version")
    return {
        "status": "ok",
        "run_dir": str(root),
        "checkpoint_id": checkpoint_id,
        "checkpoint": str(checkpoint),
        "checkpoint_exists": checkpoint.exists(),
        "tokenizer_path": str(tokenizer),
        "tokenizer_exists": tokenizer.exists(),
        "tokenizer": _pick(training, "tokenizer") or _pick(train_config, "tokenizer") or _pick(model_report, "tokenizer"),
        "model_config": config or None,
        "parameter_count": _pick(model, "parameter_count") or _pick(model_report, "total_parameters"),
        "data_source": _pick(data, "source"),
        "dataset_version": _pick(version_summary, "id") or _nested_pick(dataset_version, "dataset", "id"),
        "dataset_fingerprint": _pick(version_summary, "short_fingerprint") or _nested_pick(dataset_version, "stats", "short_fingerprint"),
        "git": _pick(manifest, "git"),
        "artifact_count": _artifact_count(manifest),
    }


def discover_checkpoint_options(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    *,
    tokenizer_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> list[CheckpointOption]:
    root = Path(run_dir)
    default_path = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    paths: list[tuple[Path, str]] = [(default_path, "default")]
    if checkpoint_candidates:
        paths.extend((Path(path), "candidate") for path in checkpoint_candidates)
    else:
        paths.extend((path, "run-root") for path in sorted(root.glob("*.pt")))
        checkpoint_dir = root / "checkpoints"
        if checkpoint_dir.exists():
            paths.extend((path, "checkpoints") for path in sorted(checkpoint_dir.glob("*.pt")))
        paths.extend((path, "nested-run") for path in sorted(root.glob("*/checkpoint.pt")))

    options: list[CheckpointOption] = []
    seen: set[str] = set()
    used_ids: set[str] = set()
    default_key = _path_key(default_path)
    for path, source in paths:
        key = _path_key(path)
        if key in seen:
            continue
        seen.add(key)
        is_default = key == default_key
        option_id = _unique_checkpoint_id(_checkpoint_id(root, path, is_default=is_default), used_ids)
        option_tokenizer = Path(tokenizer_path) if tokenizer_path is not None and is_default else path.parent / "tokenizer.json"
        options.append(
            CheckpointOption(
                id=option_id,
                name=path.parent.name if path.name == "checkpoint.pt" and path.parent != root else path.stem,
                path=str(path),
                exists=path.exists(),
                is_default=is_default,
                tokenizer_path=str(option_tokenizer),
                tokenizer_exists=option_tokenizer.exists(),
                source=source,
            )
        )
    options.sort(key=lambda item: (not item.is_default, item.id))
    return options


def build_checkpoints_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> dict[str, Any]:
    options = discover_checkpoint_options(
        run_dir,
        checkpoint_path,
        tokenizer_path=tokenizer_path,
        checkpoint_candidates=checkpoint_candidates,
    )
    return {
        "status": "ok",
        "run_dir": str(Path(run_dir)),
        "default_checkpoint_id": options[0].id if options else None,
        "checkpoint_count": len(options),
        "checkpoints": [option.to_dict() for option in options],
    }


def build_checkpoint_compare_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    options = discover_checkpoint_options(
        root,
        checkpoint_path,
        tokenizer_path=tokenizer_path,
        checkpoint_candidates=checkpoint_candidates,
    )
    rows = [_checkpoint_compare_row(root, option) for option in options]
    baseline = rows[0] if rows else None
    for row in rows:
        _attach_checkpoint_deltas(row, baseline)
    return {
        "status": "ok",
        "run_dir": str(root),
        "default_checkpoint_id": options[0].id if options else None,
        "checkpoint_count": len(rows),
        "summary": {
            "existing_count": sum(1 for row in rows if row["exists"]),
            "missing_count": sum(1 for row in rows if not row["exists"]),
            "tokenizer_ready_count": sum(1 for row in rows if row["tokenizer_exists"]),
            "ready_count": sum(1 for row in rows if row["status"] == "ready"),
        },
        "checkpoints": rows,
    }


def resolve_checkpoint_option(options: list[CheckpointOption], selector: str | None = None) -> CheckpointOption:
    if not options:
        raise ValueError("no checkpoints are configured")
    if selector is None:
        return options[0]
    wanted = selector.strip()
    if not wanted:
        return options[0]
    if wanted.isdigit():
        index = int(wanted) - 1
        if 0 <= index < len(options):
            option = options[index]
            if not option.exists:
                raise ValueError(f"checkpoint does not exist: {option.id}")
            return option
    for option in options:
        if wanted in {option.id, option.name, option.path, Path(option.path).name}:
            if not option.exists:
                raise ValueError(f"checkpoint does not exist: {option.id}")
            return option
    raise ValueError(f"checkpoint selector did not match an allowed checkpoint: {selector}")


def append_inference_log(path: str | Path, event: dict[str, Any]) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": _utc_now(), **event}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def sse_message(event: str, data: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")


def write_pair_generation_artifacts(
    run_dir: str | Path,
    payload: dict[str, Any],
    output_dir: str | Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    out_dir = Path(output_dir) if output_dir is not None else root / "pair_generations"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = created_at or _utc_now()
    left_id = _pick_dict(payload, "left").get("checkpoint_id") or "left"
    right_id = _pick_dict(payload, "right").get("checkpoint_id") or "right"
    stem = _unique_artifact_stem(out_dir, f"{_timestamp_slug(timestamp)}-{_slug(left_id)}-vs-{_slug(right_id)}")
    json_path = out_dir / f"{stem}.json"
    html_path = out_dir / f"{stem}.html"
    record = {
        "schema_version": 1,
        "kind": "minigpt_pair_generation",
        "created_at": timestamp,
        "run_dir": str(root),
        "request": {
            "prompt": payload.get("prompt"),
            "max_new_tokens": payload.get("max_new_tokens"),
            "temperature": payload.get("temperature"),
            "top_k": payload.get("top_k"),
            "seed": payload.get("seed"),
        },
        "left": payload.get("left"),
        "right": payload.get("right"),
        "comparison": payload.get("comparison"),
        "artifact": {
            "json_path": str(json_path),
            "html_path": str(html_path),
            "json_href": _artifact_href(root, json_path),
            "html_href": _artifact_href(root, html_path),
        },
    }
    json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_pair_generation_html(record), encoding="utf-8")
    return record["artifact"]


def render_pair_generation_html(record: dict[str, Any]) -> str:
    left = _pick_dict(record, "left")
    right = _pick_dict(record, "right")
    comparison = _pick_dict(record, "comparison")
    request = _pick_dict(record, "request")
    rows = [
        ("Created", record.get("created_at")),
        ("Prompt", request.get("prompt")),
        ("Max tokens", request.get("max_new_tokens")),
        ("Temperature", request.get("temperature")),
        ("Top-k", request.get("top_k")),
        ("Seed", request.get("seed")),
        ("Left checkpoint", left.get("checkpoint_id")),
        ("Right checkpoint", right.get("checkpoint_id")),
        ("Generated equal", comparison.get("generated_equal")),
        ("Generated char delta", comparison.get("generated_char_delta")),
        ("Continuation equal", comparison.get("continuation_equal")),
        ("Continuation char delta", comparison.get("continuation_char_delta")),
    ]
    table = "".join(f"<tr><th>{_html(label)}</th><td>{_html(value)}</td></tr>" for label, value in rows)
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>MiniGPT pair generation {_html(record.get('created_at'))}</title>",
            "<style>",
            "body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;color:#172033;background:#f6f8fa;line-height:1.5}",
            "main{max-width:1100px;margin:auto;background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:20px}",
            "table{width:100%;border-collapse:collapse;margin:12px 0 18px}th,td{border-bottom:1px solid #d8dee4;padding:8px;text-align:left;vertical-align:top}",
            ".grid{display:grid;grid-template-columns:repeat(2,minmax(260px,1fr));gap:14px}.panel{border:1px solid #d8dee4;border-radius:8px;padding:12px;background:#fbfcfd}",
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eef3f7;border-radius:7px;padding:10px;min-height:120px}",
            "@media(max-width:760px){.grid{grid-template-columns:1fr}body{margin:12px}}",
            "</style>",
            "</head>",
            "<body><main>",
            "<h1>MiniGPT Pair Generation</h1>",
            f"<table>{table}</table>",
            '<section class="grid">',
            f"<article class=\"panel\"><h2>Left: {_html(left.get('checkpoint_id'))}</h2><pre>{_html(left.get('generated'))}</pre></article>",
            f"<article class=\"panel\"><h2>Right: {_html(right.get('checkpoint_id'))}</h2><pre>{_html(right.get('generated'))}</pre></article>",
            "</section>",
            "</main></body></html>",
        ]
    )


def create_handler(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    generator_factory: Callable[[str | Path, str | Path | None, str], Any] = MiniGPTGenerator,
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> type[BaseHTTPRequestHandler]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    safety = safety_profile or InferenceSafetyProfile()
    request_log = Path(request_log_path) if request_log_path is not None else root / "inference_requests.jsonl"
    checkpoint_options = discover_checkpoint_options(root, checkpoint, tokenizer_path=tokenizer_path, checkpoint_candidates=checkpoint_candidates)
    generators: dict[str, Any] = {}

    def generator_for(option: CheckpointOption) -> Any:
        if option.id not in generators:
            selected_tokenizer = Path(option.tokenizer_path) if option.tokenizer_path is not None else tokenizer_path
            generators[option.id] = generator_factory(option.path, selected_tokenizer, device)
        return generators[option.id]

    class MiniGPTServerHandler(BaseHTTPRequestHandler):
        server_version = "MiniGPTServer/0.5"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._send_json(
                    build_health_payload(
                        root,
                        checkpoint,
                        safety_profile=safety,
                        request_log_path=request_log,
                        checkpoint_candidates=checkpoint_candidates,
                    )
                )
                return
            if parsed.path == "/api/checkpoints":
                self._send_json(build_checkpoints_payload(root, checkpoint, tokenizer_path, checkpoint_candidates))
                return
            if parsed.path == "/api/checkpoint-compare":
                self._send_json(build_checkpoint_compare_payload(root, checkpoint, tokenizer_path, checkpoint_candidates))
                return
            if parsed.path == "/api/model-info":
                selector = _query_value(parsed.query, "checkpoint")
                try:
                    option = resolve_checkpoint_option(checkpoint_options, selector)
                except ValueError as exc:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._send_json(build_model_info_payload(_metadata_run_dir(root, option), option.path, option.tokenizer_path, option.id))
                return
            if parsed.path in {"/", "/playground.html"}:
                html_path = root / "playground.html"
                if not html_path.exists():
                    write_playground(root, output_path=html_path)
                self._send_file(html_path)
                return
            self._serve_run_file(parsed.path)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/generate-pair-artifact":
                self._handle_generate_pair(save_artifact=True)
                return
            if parsed.path == "/api/generate-pair":
                self._handle_generate_pair()
                return
            if parsed.path == "/api/generate-stream":
                self._handle_generate_stream()
                return
            if parsed.path != "/api/generate":
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            request: GenerationRequest | None = None
            option: CheckpointOption | None = None
            try:
                payload = self._read_json_body()
                request = parse_generation_request(payload, safety)
                option = resolve_checkpoint_option(checkpoint_options, request.checkpoint)
                if not option.exists:
                    raise ValueError(f"checkpoint does not exist: {option.id}")
                response = generator_for(option).generate(request)
            except ValueError as exc:
                self._log_generation("bad_request", request=request, checkpoint_option=option, error=str(exc))
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._log_generation("error", request=request, checkpoint_option=option, error=str(exc))
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._log_generation("ok", request=request, response=response, checkpoint_option=option)
            payload = response.to_dict()
            payload["checkpoint_id"] = option.id
            self._send_json(payload)

        def _handle_generate_stream(self) -> None:
            request: GenerationRequest | None = None
            option: CheckpointOption | None = None
            response: GenerationResponse | None = None
            chunk_count = 0
            stream_open = False
            try:
                payload = self._read_json_body()
                request = parse_generation_request(payload, safety)
                option = resolve_checkpoint_option(checkpoint_options, request.checkpoint)
                if not option.exists:
                    raise ValueError(f"checkpoint does not exist: {option.id}")
                self._send_sse_headers()
                stream_open = True
                self._write_sse(
                    "start",
                    {
                        "prompt": request.prompt,
                        "max_new_tokens": request.max_new_tokens,
                        "temperature": request.temperature,
                        "top_k": request.top_k,
                        "seed": request.seed,
                        "checkpoint_id": option.id,
                        "checkpoint": option.path,
                    },
                )
                generated = request.prompt
                continuation = ""
                tokenizer = "unknown"
                checkpoint_path = option.path
                for chunk in generator_for(option).stream(request):
                    chunk_count += 1
                    chunk_payload = chunk.to_dict()
                    chunk_payload["checkpoint_id"] = option.id
                    generated = chunk.generated
                    continuation = chunk.continuation
                    tokenizer = chunk.tokenizer
                    checkpoint_path = chunk.checkpoint
                    self._write_sse("token", chunk_payload)
                response = GenerationResponse(
                    prompt=request.prompt,
                    generated=generated,
                    continuation=continuation,
                    max_new_tokens=request.max_new_tokens,
                    temperature=request.temperature,
                    top_k=request.top_k,
                    seed=request.seed,
                    checkpoint=checkpoint_path,
                    tokenizer=tokenizer,
                    checkpoint_id=option.id,
                )
                self._write_sse(
                    "end",
                    {
                        "done": True,
                        "chunk_count": chunk_count,
                        "response": response.to_dict(),
                    },
                )
            except ValueError as exc:
                self._log_generation(
                    "bad_request",
                    request=request,
                    checkpoint_option=option,
                    error=str(exc),
                    endpoint="/api/generate-stream",
                )
                if stream_open:
                    self._write_sse("error", {"error": str(exc)})
                else:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._log_generation(
                    "error",
                    request=request,
                    response=response,
                    checkpoint_option=option,
                    error=str(exc),
                    endpoint="/api/generate-stream",
                    stream_chunks=chunk_count,
                )
                if stream_open:
                    self._write_sse("error", {"error": str(exc)})
                else:
                    self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._log_generation(
                "ok",
                request=request,
                response=response,
                checkpoint_option=option,
                endpoint="/api/generate-stream",
                stream_chunks=chunk_count,
            )

        def _handle_generate_pair(self, *, save_artifact: bool = False) -> None:
            endpoint = "/api/generate-pair-artifact" if save_artifact else "/api/generate-pair"
            pair_request: GenerationPairRequest | None = None
            left_option: CheckpointOption | None = None
            right_option: CheckpointOption | None = None
            left_response: GenerationResponse | None = None
            right_response: GenerationResponse | None = None
            artifact: dict[str, Any] | None = None
            try:
                payload = self._read_json_body()
                pair_request = parse_generation_pair_request(payload, safety)
                left_option = resolve_checkpoint_option(checkpoint_options, pair_request.left.checkpoint)
                right_option = resolve_checkpoint_option(checkpoint_options, pair_request.right.checkpoint)
                if not left_option.exists:
                    raise ValueError(f"checkpoint does not exist: {left_option.id}")
                if not right_option.exists:
                    raise ValueError(f"checkpoint does not exist: {right_option.id}")
                left_response = generator_for(left_option).generate(pair_request.left)
                right_response = generator_for(right_option).generate(pair_request.right)
            except ValueError as exc:
                self._log_pair_generation(
                    "bad_request",
                    pair_request=pair_request,
                    left_option=left_option,
                    right_option=right_option,
                    error=str(exc),
                    endpoint=endpoint,
                )
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._log_pair_generation(
                    "error",
                    pair_request=pair_request,
                    left_option=left_option,
                    right_option=right_option,
                    left_response=left_response,
                    right_response=right_response,
                    error=str(exc),
                    endpoint=endpoint,
                )
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            payload = _pair_generation_payload(pair_request, left_option, right_option, left_response, right_response)
            if save_artifact:
                artifact = write_pair_generation_artifacts(root, payload)
                payload["artifact"] = artifact
            self._log_pair_generation(
                "ok",
                pair_request=pair_request,
                left_option=left_option,
                right_option=right_option,
                left_response=left_response,
                right_response=right_response,
                artifact=artifact,
                endpoint=endpoint,
            )
            self._send_json(payload)

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _serve_run_file(self, request_path: str) -> None:
            relative = unquote(request_path.lstrip("/"))
            target = (root / relative).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError:
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            if not target.exists() or not target.is_file():
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_file(target)

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length > safety.max_body_bytes:
                raise ValueError(f"request body must be at most {safety.max_body_bytes} bytes")
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body or "{}")
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _log_generation(
            self,
            status: str,
            *,
            request: GenerationRequest | None = None,
            response: GenerationResponse | None = None,
            checkpoint_option: CheckpointOption | None = None,
            error: str | None = None,
            endpoint: str = "/api/generate",
            stream_chunks: int | None = None,
        ) -> None:
            event: dict[str, Any] = {
                "endpoint": endpoint,
                "status": status,
                "client": self.client_address[0] if self.client_address else None,
                "checkpoint": checkpoint_option.path if checkpoint_option is not None else str(checkpoint),
                "checkpoint_id": checkpoint_option.id if checkpoint_option is not None else None,
            }
            if request is not None:
                event.update(
                    {
                        "requested_checkpoint": request.checkpoint,
                        "prompt_chars": len(request.prompt),
                        "max_new_tokens": request.max_new_tokens,
                        "temperature": request.temperature,
                        "top_k": request.top_k,
                        "seed": request.seed,
                    }
                )
            if response is not None:
                event["generated_chars"] = len(response.generated)
                event["continuation_chars"] = len(response.continuation)
                event["tokenizer"] = response.tokenizer
            if stream_chunks is not None:
                event["stream_chunks"] = stream_chunks
            if error is not None:
                event["error"] = error
            append_inference_log(request_log, event)

        def _log_pair_generation(
            self,
            status: str,
            *,
            pair_request: GenerationPairRequest | None = None,
            left_option: CheckpointOption | None = None,
            right_option: CheckpointOption | None = None,
            left_response: GenerationResponse | None = None,
            right_response: GenerationResponse | None = None,
            artifact: dict[str, Any] | None = None,
            error: str | None = None,
            endpoint: str = "/api/generate-pair",
        ) -> None:
            event: dict[str, Any] = {
                "endpoint": endpoint,
                "status": status,
                "client": self.client_address[0] if self.client_address else None,
                "left_checkpoint": left_option.path if left_option is not None else None,
                "left_checkpoint_id": left_option.id if left_option is not None else None,
                "right_checkpoint": right_option.path if right_option is not None else None,
                "right_checkpoint_id": right_option.id if right_option is not None else None,
            }
            if pair_request is not None:
                event.update(
                    {
                        "requested_left_checkpoint": pair_request.left.checkpoint,
                        "requested_right_checkpoint": pair_request.right.checkpoint,
                        "prompt_chars": len(pair_request.left.prompt),
                        "max_new_tokens": pair_request.left.max_new_tokens,
                        "temperature": pair_request.left.temperature,
                        "top_k": pair_request.left.top_k,
                        "seed": pair_request.left.seed,
                    }
                )
            if left_response is not None:
                event["left_generated_chars"] = len(left_response.generated)
                event["left_continuation_chars"] = len(left_response.continuation)
            if right_response is not None:
                event["right_generated_chars"] = len(right_response.generated)
                event["right_continuation_chars"] = len(right_response.continuation)
            if left_response is not None and right_response is not None:
                event["generated_equal"] = left_response.generated == right_response.generated
                event["continuation_equal"] = left_response.continuation == right_response.continuation
            if artifact is not None:
                event["artifact_json"] = artifact.get("json_path")
                event["artifact_html"] = artifact.get("html_path")
            if error is not None:
                event["error"] = error
            append_inference_log(request_log, event)

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _send_sse_headers(self) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def _write_sse(self, event: str, data: dict[str, Any]) -> None:
            self.wfile.write(sse_message(event, data))
            self.wfile.flush()

        def _send_file(self, path: Path) -> None:
            body = path.read_bytes()
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return MiniGPTServerHandler


def run_server(
    run_dir: str | Path,
    host: str = "127.0.0.1",
    port: int = 8000,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
    checkpoint_candidates: list[str | Path] | None = None,
) -> ThreadingHTTPServer:
    handler = create_handler(
        run_dir,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        safety_profile=safety_profile,
        request_log_path=request_log_path,
        checkpoint_candidates=checkpoint_candidates,
    )
    server = ThreadingHTTPServer((host, port), handler)
    return server


def _as_int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _as_float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc


def _empty_top_k(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() in {"", "0", "none", "None"}
    return value == 0


def _query_value(query: str, key: str) -> str | None:
    values = parse_qs(query).get(key)
    if not values:
        return None
    return values[0]


def _path_key(path: str | Path) -> str:
    return str(Path(path).resolve()).casefold()


def _checkpoint_id(root: Path, path: Path, *, is_default: bool) -> str:
    if is_default:
        return "default"
    try:
        relative = path.resolve().relative_to(root.resolve())
        if relative.name == "checkpoint.pt" and len(relative.parts) > 1:
            return _slug(relative.parts[-2])
        return _slug(relative.with_suffix("").as_posix())
    except ValueError:
        if path.name == "checkpoint.pt" and path.parent.name:
            return _slug(path.parent.name)
        return _slug(path.stem)


def _unique_checkpoint_id(base: str, used: set[str]) -> str:
    candidate = base or "checkpoint"
    index = 2
    while candidate in used:
        candidate = f"{base}-{index}"
        index += 1
    used.add(candidate)
    return candidate


def _slug(value: Any) -> str:
    text = str(value).replace("\\", "/").strip().strip("/")
    output = []
    for char in text:
        if char.isalnum():
            output.append(char.lower())
        elif char in {"-", "_", ".", "/"}:
            output.append("-")
        else:
            output.append("-")
    slug = "".join(output).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "checkpoint"


def _checkpoint_compare_row(root: Path, option: CheckpointOption) -> dict[str, Any]:
    checkpoint_path = Path(option.path)
    size_bytes: int | None = None
    modified_utc: str | None = None
    if checkpoint_path.exists() and checkpoint_path.is_file():
        stat = checkpoint_path.stat()
        size_bytes = stat.st_size
        modified_utc = datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata_root = _metadata_run_dir(root, option)
    info = build_model_info_payload(metadata_root, checkpoint_path, option.tokenizer_path, option.id)
    notes: list[str] = []
    if not option.exists:
        notes.append("checkpoint missing")
    if not option.tokenizer_exists:
        notes.append("tokenizer missing")
    if info.get("model_config") is None:
        notes.append("model config missing")
    if info.get("dataset_version") is None:
        notes.append("dataset version missing")
    status = "ready" if option.exists and option.tokenizer_exists else "incomplete"
    return {
        **option.to_dict(),
        "status": status,
        "size_bytes": size_bytes,
        "modified_utc": modified_utc,
        "metadata_run_dir": str(metadata_root),
        "model_info_endpoint": f"/api/model-info?checkpoint={option.id}",
        "tokenizer": info.get("tokenizer"),
        "parameter_count": info.get("parameter_count"),
        "dataset_version": info.get("dataset_version"),
        "dataset_fingerprint": info.get("dataset_fingerprint"),
        "model_config": info.get("model_config"),
        "artifact_count": info.get("artifact_count"),
        "notes": notes,
    }


def _attach_checkpoint_deltas(row: dict[str, Any], baseline: dict[str, Any] | None) -> None:
    if baseline is None:
        row["size_delta_bytes"] = None
        row["parameter_delta"] = None
        row["same_tokenizer"] = None
        row["same_dataset_version"] = None
        row["same_dataset_fingerprint"] = None
        row["same_model_config"] = None
        return
    row["size_delta_bytes"] = _numeric_delta(row.get("size_bytes"), baseline.get("size_bytes"))
    row["parameter_delta"] = _numeric_delta(row.get("parameter_count"), baseline.get("parameter_count"))
    row["same_tokenizer"] = _same_known(row.get("tokenizer"), baseline.get("tokenizer"))
    row["same_dataset_version"] = _same_known(row.get("dataset_version"), baseline.get("dataset_version"))
    row["same_dataset_fingerprint"] = _same_known(row.get("dataset_fingerprint"), baseline.get("dataset_fingerprint"))
    row["same_model_config"] = _same_known(row.get("model_config"), baseline.get("model_config"))


def _metadata_run_dir(root: Path, option: CheckpointOption) -> Path:
    checkpoint_parent = Path(option.path).parent
    metadata_files = ("run_manifest.json", "train_config.json", "dataset_version.json")
    if checkpoint_parent != root and any((checkpoint_parent / name).exists() for name in metadata_files):
        return checkpoint_parent
    return root


def _numeric_delta(value: Any, baseline: Any) -> int | float | None:
    if isinstance(value, (int, float)) and isinstance(baseline, (int, float)):
        return value - baseline
    return None


def _same_known(value: Any, baseline: Any) -> bool | None:
    if value is None or baseline is None:
        return None
    return value == baseline


def _artifact_href(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _timestamp_slug(value: str) -> str:
    return _slug(value.replace("Z", "utc"))


def _unique_artifact_stem(out_dir: Path, base: str) -> str:
    stem = base or "pair-generation"
    candidate = stem
    index = 2
    while (out_dir / f"{candidate}.json").exists() or (out_dir / f"{candidate}.html").exists():
        candidate = f"{stem}-{index}"
        index += 1
    return candidate


def _html(value: Any) -> str:
    return html_lib.escape("" if value is None else str(value), quote=True)


def _pair_generation_payload(
    pair_request: GenerationPairRequest,
    left_option: CheckpointOption,
    right_option: CheckpointOption,
    left_response: GenerationResponse,
    right_response: GenerationResponse,
) -> dict[str, Any]:
    left_payload = left_response.to_dict()
    right_payload = right_response.to_dict()
    left_payload["checkpoint_id"] = left_option.id
    right_payload["checkpoint_id"] = right_option.id
    return {
        "status": "ok",
        "prompt": pair_request.left.prompt,
        "max_new_tokens": pair_request.left.max_new_tokens,
        "temperature": pair_request.left.temperature,
        "top_k": pair_request.left.top_k,
        "seed": pair_request.left.seed,
        "left": left_payload,
        "right": right_payload,
        "comparison": {
            "same_checkpoint": left_option.id == right_option.id,
            "generated_equal": left_response.generated == right_response.generated,
            "continuation_equal": left_response.continuation == right_response.continuation,
            "left_generated_chars": len(left_response.generated),
            "right_generated_chars": len(right_response.generated),
            "generated_char_delta": len(right_response.generated) - len(left_response.generated),
            "left_continuation_chars": len(left_response.continuation),
            "right_continuation_chars": len(right_response.continuation),
            "continuation_char_delta": len(right_response.continuation) - len(left_response.continuation),
        },
    }


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _pick(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        return payload.get(key)
    return None


def _pick_dict(payload: Any, key: str) -> dict[str, Any]:
    value = _pick(payload, key)
    return value if isinstance(value, dict) else {}


def _nested_pick(payload: Any, *keys: str) -> Any:
    value = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _artifact_count(manifest: Any) -> int | None:
    artifacts = _pick(manifest, "artifacts")
    if not isinstance(artifacts, list):
        return None
    return sum(1 for item in artifacts if isinstance(item, dict) and item.get("exists"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
