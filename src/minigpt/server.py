from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from functools import partial
import json
import mimetypes
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import unquote, urlparse

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
class GenerationRequest:
    prompt: str
    max_new_tokens: int
    temperature: float
    top_k: int | None
    seed: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    return GenerationRequest(
        prompt=prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
        seed=seed,
    )


def build_health_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    *,
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    request_log = Path(request_log_path) if request_log_path is not None else root / "inference_requests.jsonl"
    safety = safety_profile or InferenceSafetyProfile()
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
        "safety": safety.to_dict(),
        "request_log": str(request_log),
        "request_log_exists": request_log.exists(),
    }


def build_model_info_payload(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
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


def append_inference_log(path: str | Path, event: dict[str, Any]) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": _utc_now(), **event}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def create_handler(
    run_dir: str | Path,
    checkpoint_path: str | Path | None = None,
    tokenizer_path: str | Path | None = None,
    device: str = "auto",
    generator_factory: Callable[[str | Path, str | Path | None, str], Any] = MiniGPTGenerator,
    safety_profile: InferenceSafetyProfile | None = None,
    request_log_path: str | Path | None = None,
) -> type[BaseHTTPRequestHandler]:
    root = Path(run_dir)
    checkpoint = Path(checkpoint_path) if checkpoint_path is not None else root / "checkpoint.pt"
    generator = generator_factory(checkpoint, tokenizer_path, device)
    safety = safety_profile or InferenceSafetyProfile()
    request_log = Path(request_log_path) if request_log_path is not None else root / "inference_requests.jsonl"

    class MiniGPTServerHandler(BaseHTTPRequestHandler):
        server_version = "MiniGPTServer/0.2"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._send_json(build_health_payload(root, checkpoint, safety_profile=safety, request_log_path=request_log))
                return
            if parsed.path == "/api/model-info":
                self._send_json(build_model_info_payload(root, checkpoint, tokenizer_path))
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
            if parsed.path != "/api/generate":
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return
            request: GenerationRequest | None = None
            try:
                payload = self._read_json_body()
                request = parse_generation_request(payload, safety)
                response = generator.generate(request)
            except ValueError as exc:
                self._log_generation("bad_request", request=request, error=str(exc))
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            except Exception as exc:
                self._log_generation("error", request=request, error=str(exc))
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._log_generation("ok", request=request, response=response)
            self._send_json(response.to_dict())

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
            error: str | None = None,
        ) -> None:
            event: dict[str, Any] = {
                "endpoint": "/api/generate",
                "status": status,
                "client": self.client_address[0] if self.client_address else None,
                "checkpoint": str(checkpoint),
            }
            if request is not None:
                event.update(
                    {
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
) -> ThreadingHTTPServer:
    handler = create_handler(
        run_dir,
        checkpoint_path=checkpoint_path,
        tokenizer_path=tokenizer_path,
        device=device,
        safety_profile=safety_profile,
        request_log_path=request_log_path,
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
