from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.chat import (
    ChatTurn,
    assistant_reply_from_generation,
    build_chat_prompt,
    prepare_chat_prompt,
    turns_to_dicts,
)
from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import Tokenizer, load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny chat wrapper around a MiniGPT checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--message", type=str, default=None, help="Run one chat turn instead of interactive mode")
    parser.add_argument("--system", type=str, default="你是一个简洁的中文学习助手。")
    parser.add_argument("--max-new-tokens", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-k", type=int, default=30, help="Use 0 to disable top-k filtering")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--out", type=Path, default=None, help="Optional transcript JSON path")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


def load_model(
    checkpoint_path: Path,
    tokenizer_path: Path | None,
    device: torch.device,
) -> tuple[MiniGPT, Tokenizer]:
    tokenizer_file = tokenizer_path or checkpoint_path.parent / "tokenizer.json"
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_file)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, tokenizer


@torch.no_grad()
def generate_reply(
    model: MiniGPT,
    tokenizer: Tokenizer,
    system_prompt: str,
    turns: list[ChatTurn],
    max_new_tokens: int,
    temperature: float,
    top_k: int | None,
    device: torch.device,
) -> tuple[str, dict[str, object]]:
    prompt = build_chat_prompt(turns, system_prompt=system_prompt, add_assistant_prompt=True)
    prepared = prepare_chat_prompt(tokenizer, prompt, model.config.block_size)
    idx = torch.tensor([prepared.token_ids], dtype=torch.long, device=device)
    out = model.generate(
        idx,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
    )
    generated = tokenizer.decode(out[0].tolist())
    reply = assistant_reply_from_generation(generated, prepared.decoded_context)
    metadata: dict[str, object] = {
        "prompt": prepared.text,
        "decoded_context": prepared.decoded_context,
        "context_token_ids": prepared.token_ids,
        "original_token_count": prepared.original_token_count,
        "context_trimmed": prepared.trimmed,
        "raw_generation": generated,
    }
    return reply, metadata


def write_transcript(
    path: Path,
    system_prompt: str,
    turns: list[ChatTurn],
    metadata: dict[str, object],
    tokenizer_name: str,
    checkpoint: Path,
    temperature: float,
    top_k: int | None,
) -> None:
    payload = {
        "checkpoint": str(checkpoint),
        "tokenizer": tokenizer_name,
        "system": system_prompt,
        "turns": turns_to_dicts(turns),
        "generation": {
            "temperature": temperature,
            "top_k": top_k,
        },
        "metadata": metadata,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_one_shot(args: argparse.Namespace, model: MiniGPT, tokenizer: Tokenizer, device: torch.device) -> None:
    if args.message is None:
        raise ValueError("one-shot mode requires --message")

    top_k = None if args.top_k <= 0 else args.top_k
    turns = [ChatTurn("user", args.message)]
    reply, metadata = generate_reply(
        model=model,
        tokenizer=tokenizer,
        system_prompt=args.system,
        turns=turns,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        top_k=top_k,
        device=device,
    )
    turns.append(ChatTurn("assistant", reply or "[empty]"))

    print(f"tokenizer={getattr(tokenizer, 'name', 'unknown')}")
    print(f"context_tokens={len(metadata['context_token_ids'])}")
    print(f"context_trimmed={metadata['context_trimmed']}")
    print(f"assistant={reply}")
    if args.out is not None:
        write_transcript(
            args.out,
            system_prompt=args.system,
            turns=turns,
            metadata=metadata,
            tokenizer_name=getattr(tokenizer, "name", "unknown"),
            checkpoint=args.checkpoint,
            temperature=args.temperature,
            top_k=top_k,
        )
        print(f"saved={args.out}")


def run_interactive(args: argparse.Namespace, model: MiniGPT, tokenizer: Tokenizer, device: torch.device) -> None:
    top_k = None if args.top_k <= 0 else args.top_k
    turns: list[ChatTurn] = []
    latest_metadata: dict[str, object] = {}

    print("MiniGPT chat. Type /exit to stop.")
    while True:
        message = input("user> ").strip()
        if message in {"/exit", "/quit"}:
            break
        if not message:
            continue
        turns.append(ChatTurn("user", message))
        reply, latest_metadata = generate_reply(
            model=model,
            tokenizer=tokenizer,
            system_prompt=args.system,
            turns=turns,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=top_k,
            device=device,
        )
        print(f"assistant> {reply}")
        turns.append(ChatTurn("assistant", reply or "[empty]"))

    if args.out is not None:
        write_transcript(
            args.out,
            system_prompt=args.system,
            turns=turns,
            metadata=latest_metadata,
            tokenizer_name=getattr(tokenizer, "name", "unknown"),
            checkpoint=args.checkpoint,
            temperature=args.temperature,
            top_k=top_k,
        )
        print(f"saved={args.out}")


def main() -> None:
    args = parse_args()
    if args.max_new_tokens < 1:
        raise ValueError("--max-new-tokens must be at least 1")
    if args.temperature <= 0:
        raise ValueError("--temperature must be greater than 0")
    if args.top_k < 0:
        raise ValueError("--top-k must be greater than or equal to 0")

    device = choose_device(args.device)
    model, tokenizer = load_model(args.checkpoint, args.tokenizer, device)
    if args.message is not None:
        run_one_shot(args, model, tokenizer, device)
    else:
        run_interactive(args, model, tokenizer, device)


if __name__ == "__main__":
    main()
