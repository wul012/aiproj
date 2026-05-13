from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.server import InferenceSafetyProfile, discover_checkpoint_options, run_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve MiniGPT playground and local generation API.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--checkpoint-candidate", type=Path, action="append", default=[], help="Additional selectable checkpoint path, repeatable")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-prompt-chars", type=int, default=2000)
    parser.add_argument("--max-new-tokens-limit", type=int, default=512)
    parser.add_argument("--min-temperature", type=float, default=0.05)
    parser.add_argument("--max-temperature", type=float, default=2.0)
    parser.add_argument("--max-top-k", type=int, default=200)
    parser.add_argument("--max-body-bytes", type=int, default=16 * 1024)
    parser.add_argument("--max-stream-seconds", type=float, default=30.0)
    parser.add_argument("--request-log", type=Path, default=None, help="JSONL log path. Defaults to <run-dir>/inference_requests.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    safety = InferenceSafetyProfile(
        max_prompt_chars=args.max_prompt_chars,
        max_new_tokens=args.max_new_tokens_limit,
        min_temperature=args.min_temperature,
        max_temperature=args.max_temperature,
        max_top_k=args.max_top_k,
        max_body_bytes=args.max_body_bytes,
        max_stream_seconds=args.max_stream_seconds,
    )
    server = run_server(
        args.run_dir,
        host=args.host,
        port=args.port,
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
        safety_profile=safety,
        request_log_path=args.request_log,
        checkpoint_candidates=args.checkpoint_candidate or None,
    )
    checkpoint_options = discover_checkpoint_options(
        args.run_dir,
        args.checkpoint,
        tokenizer_path=args.tokenizer,
        checkpoint_candidates=args.checkpoint_candidate or None,
    )
    url = f"http://{args.host}:{server.server_port}/"
    print(f"serving={url}", flush=True)
    print(f"run_dir={args.run_dir}", flush=True)
    print(f"model_info={url}api/model-info", flush=True)
    print(f"generate_stream={url}api/generate-stream", flush=True)
    print(f"generate_pair={url}api/generate-pair", flush=True)
    print(f"generate_pair_artifact={url}api/generate-pair-artifact", flush=True)
    print(f"request_history={url}api/request-history", flush=True)
    print(f"checkpoints={url}api/checkpoints", flush=True)
    print(f"checkpoint_compare={url}api/checkpoint-compare", flush=True)
    print(f"checkpoint_count={len(checkpoint_options)}", flush=True)
    print(f"request_log={args.request_log or args.run_dir / 'inference_requests.jsonl'}", flush=True)
    print(f"safety={safety.to_dict()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopping", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
