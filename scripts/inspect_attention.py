from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a MiniGPT attention map for a prompt.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "runs" / "minigpt" / "checkpoint.pt")
    parser.add_argument("--tokenizer", type=Path, default=None)
    parser.add_argument("--prompt", type=str, default="人工智能")
    parser.add_argument("--layer", type=int, default=0)
    parser.add_argument("--head", type=int, default=0)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


def token_label(token: str, limit: int = 8) -> str:
    label = token.replace("\n", "\\n").replace("\t", "\\t")
    if len(label) > limit:
        return label[: limit - 1] + "…"
    return label


def top_links(matrix: list[list[float]], tokens: list[str], row: int, top_k: int = 5) -> list[dict[str, object]]:
    scored = sorted(enumerate(matrix[row]), key=lambda item: item[1], reverse=True)[:top_k]
    return [
        {
            "from_index": row,
            "from_token": tokens[row],
            "to_index": col,
            "to_token": tokens[col],
            "weight": round(float(weight), 6),
        }
        for col, weight in scored
    ]


def write_svg(matrix: list[list[float]], tokens: list[str], path: Path, layer: int, head: int) -> None:
    cell = 38
    label_space = 96
    top_space = 92
    width = label_space + cell * len(tokens) + 28
    height = top_space + cell * len(tokens) + 42

    rects: list[str] = []
    for row, values in enumerate(matrix):
        for col, weight in enumerate(values):
            intensity = max(0, min(255, int(255 * (1.0 - weight))))
            color = f"rgb(255,{intensity},{intensity})"
            x = label_space + col * cell
            y = top_space + row * cell
            rects.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" stroke="#e5e7eb"/>'
            )
            if weight >= 0.01:
                rects.append(
                    f'<text x="{x + cell / 2:.1f}" y="{y + cell / 2 + 5:.1f}" '
                    f'text-anchor="middle" font-size="10" font-family="Arial" fill="#111827">{weight:.2f}</text>'
                )

    x_labels = []
    y_labels = []
    for i, token in enumerate(tokens):
        label = html.escape(token_label(token))
        x = label_space + i * cell + cell / 2
        y = top_space - 10
        x_labels.append(
            f'<text x="{x:.1f}" y="{y}" text-anchor="middle" font-size="12" '
            f'font-family="Arial" fill="#374151">{label}</text>'
        )
        y_labels.append(
            f'<text x="{label_space - 10}" y="{top_space + i * cell + cell / 2 + 4:.1f}" '
            f'text-anchor="end" font-size="12" font-family="Arial" fill="#374151">{label}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="24" y="32" font-family="Arial" font-size="18" fill="#111827">MiniGPT attention map</text>
  <text x="24" y="56" font-family="Arial" font-size="13" fill="#374151">layer={layer} head={head}; rows attend to columns</text>
  {''.join(x_labels)}
  {''.join(y_labels)}
  {''.join(rects)}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    args = parse_args()
    device = choose_device(args.device)
    tokenizer_path = args.tokenizer or args.checkpoint.parent / "tokenizer.json"
    out_dir = args.out_dir or args.checkpoint.parent / "attention"
    out_dir.mkdir(parents=True, exist_ok=True)

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    model = MiniGPT(config).to(device)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    prompt_ids = tokenizer.encode(args.prompt)
    if len(prompt_ids) > config.block_size:
        prompt_ids = prompt_ids[-config.block_size :]
    if not prompt_ids:
        raise ValueError("Prompt produced no token ids")

    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    model.set_attention_capture(True)
    with torch.no_grad():
        model(idx)
    maps = model.attention_maps()

    if args.layer < 0 or args.layer >= len(maps):
        raise ValueError(f"layer must be between 0 and {len(maps) - 1}")
    if args.head < 0 or args.head >= maps[args.layer].shape[1]:
        raise ValueError(f"head must be between 0 and {maps[args.layer].shape[1] - 1}")

    att = maps[args.layer][0, args.head]
    matrix = [[round(float(value), 6) for value in row] for row in att.tolist()]
    tokens = [tokenizer.itos[token_id] for token_id in prompt_ids]

    payload = {
        "prompt": args.prompt,
        "tokenizer": getattr(tokenizer, "name", "unknown"),
        "layer": args.layer,
        "head": args.head,
        "token_ids": prompt_ids,
        "tokens": tokens,
        "matrix": matrix,
        "last_token_top_links": top_links(matrix, tokens, row=len(tokens) - 1),
    }
    json_path = out_dir / "attention.json"
    svg_path = out_dir / "attention.svg"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_svg(matrix, tokens, svg_path, layer=args.layer, head=args.head)

    print(f"tokenizer={payload['tokenizer']}")
    print(f"tokens={tokens}")
    print(f"saved_json={json_path}")
    print(f"saved_svg={svg_path}")
    print("last_token_top_links=" + json.dumps(payload["last_token_top_links"], ensure_ascii=False))


if __name__ == "__main__":
    main()
