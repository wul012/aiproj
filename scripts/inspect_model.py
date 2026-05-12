from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT
from minigpt.model_report import build_model_report, write_model_report_svg
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a MiniGPT checkpoint architecture and parameter report.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--sequence-length", type=int, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    out_dir = args.out_dir or args.checkpoint.parent / "model_report"
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path) if tokenizer_path.exists() else None
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    report = build_model_report(
        model,
        checkpoint_metadata={
            "path": str(args.checkpoint),
            "step": checkpoint.get("step"),
            "last_loss": checkpoint.get("last_loss"),
            "tokenizer_type": checkpoint.get("tokenizer_type"),
        },
        tokenizer_name=getattr(tokenizer, "name", None),
        batch_size=args.batch_size,
        sequence_length=args.sequence_length,
    )
    json_path = out_dir / "model_report.json"
    svg_path = out_dir / "model_architecture.svg"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_model_report_svg(report, svg_path)

    print(f"model={report['model']}")
    print(f"tokenizer={report['tokenizer']}")
    print(f"total_parameters={report['total_parameters']:,}")
    print(f"owned_sum_matches_total={report['parameter_check']['owned_sum_matches_total']}")
    print("parameter_groups=" + json.dumps(report["owned_parameter_groups"], ensure_ascii=False))
    print("tensor_shapes=" + json.dumps(report["tensor_shapes"], ensure_ascii=False))
    print(f"saved_json={json_path}")
    print(f"saved_svg={svg_path}")


if __name__ == "__main__":
    main()
