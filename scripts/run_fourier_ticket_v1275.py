"""v1275 Phase A: CPU pruning probe, then budgeted GPU ticket training."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.fourier_ticket_v1275 import TicketConfig, decide, run_phase_a  # noqa: E402
from minigpt.grok_predict_v1186 import DEFAULT_CHECKPOINT  # noqa: E402
from minigpt.script_runtime import choose_device  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the preregistered v1275 Fourier-ticket experiment.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "fourier-ticket-v1275" / "cache.pt")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    device = choose_device(args.device)
    cfg = TicketConfig()
    print(f"Arm P starts on CPU: modes={cfg.modes} sparsities={cfg.sparsities}", flush=True)
    cache = run_phase_a(args.checkpoint, cfg, device)
    info = decide(cache, cfg)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(cache, args.out)
    print(f"Arm P probe={info['gates']['arm_p_probe_ok']} aligned={info['gates']['arm_p_aligned']}")
    print(f"Arm L device={device} runs={cache['arm_l']['actual_runs']}/{cache['arm_l']['max_runs']}")
    print(f"status={info['status']} verdict={info['verdict']} cache={args.out}")
    if info["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
