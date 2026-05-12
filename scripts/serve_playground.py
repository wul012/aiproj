from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.server import run_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve MiniGPT playground and local generation API.")
    parser.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = run_server(
        args.run_dir,
        host=args.host,
        port=args.port,
        checkpoint_path=args.checkpoint,
        tokenizer_path=args.tokenizer,
        device=args.device,
    )
    url = f"http://{args.host}:{server.server_port}/"
    print(f"serving={url}", flush=True)
    print(f"run_dir={args.run_dir}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopping", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
