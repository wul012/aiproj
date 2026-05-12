from __future__ import annotations

from dataclasses import asdict, dataclass
import html
from pathlib import Path
from typing import Any

import torch.nn as nn

from .model import GPTConfig, MiniGPT


@dataclass(frozen=True)
class ParameterGroup:
    name: str
    label: str
    parameters: int
    percent: float

    def to_dict(self) -> dict[str, str | int | float]:
        return asdict(self)


def count_parameters(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())


def parameter_groups(model: MiniGPT) -> list[ParameterGroup]:
    specs = [
        ("token_embedding", "Token embedding", model.token_embedding),
        ("position_embedding", "Position embedding", model.position_embedding),
        ("transformer_blocks", "Transformer blocks", model.blocks),
        ("final_layer_norm", "Final LayerNorm", model.ln_f),
    ]
    total = model.parameter_count()
    groups: list[ParameterGroup] = []
    for name, label, module in specs:
        parameters = count_parameters(module)
        percent = 0.0 if total == 0 else round(parameters * 100 / total, 4)
        groups.append(ParameterGroup(name=name, label=label, parameters=parameters, percent=percent))
    return groups


def block_parameter_groups(model: MiniGPT) -> list[dict[str, int]]:
    blocks: list[dict[str, int]] = []
    for index, block in enumerate(model.blocks):
        blocks.append(
            {
                "index": index,
                "attention": count_parameters(block.attn),
                "mlp": count_parameters(block.mlp),
                "layer_norms": count_parameters(block.ln_1) + count_parameters(block.ln_2),
                "total": count_parameters(block),
            }
        )
    return blocks


def tensor_shape_summary(config: GPTConfig, batch_size: int = 1, sequence_length: int | None = None) -> dict[str, list[int]]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    sequence_length = config.block_size if sequence_length is None else sequence_length
    if sequence_length < 1:
        raise ValueError("sequence_length must be at least 1")
    if sequence_length > config.block_size:
        raise ValueError("sequence_length cannot exceed block_size")
    if config.n_embd % config.n_head != 0:
        raise ValueError("n_embd must be divisible by n_head")

    head_size = config.n_embd // config.n_head
    return {
        "token_ids": [batch_size, sequence_length],
        "embeddings": [batch_size, sequence_length, config.n_embd],
        "qkv_split": [batch_size, config.n_head, sequence_length, head_size],
        "attention_scores": [batch_size, config.n_head, sequence_length, sequence_length],
        "block_output": [batch_size, sequence_length, config.n_embd],
        "logits": [batch_size, sequence_length, config.vocab_size],
    }


def output_head_is_tied(model: MiniGPT) -> bool:
    return model.lm_head.weight.data_ptr() == model.token_embedding.weight.data_ptr()


def build_model_report(
    model: MiniGPT,
    *,
    checkpoint_metadata: dict[str, Any] | None = None,
    tokenizer_name: str | None = None,
    batch_size: int = 1,
    sequence_length: int | None = None,
) -> dict[str, Any]:
    config = model.config
    groups = parameter_groups(model)
    owned_parameters = sum(group.parameters for group in groups)
    total_parameters = model.parameter_count()
    report = {
        "model": "MiniGPT",
        "config": asdict(config),
        "tokenizer": tokenizer_name,
        "total_parameters": total_parameters,
        "owned_parameter_groups": [group.to_dict() for group in groups],
        "owned_parameter_sum": owned_parameters,
        "transformer_blocks": block_parameter_groups(model),
        "tensor_shapes": tensor_shape_summary(config, batch_size=batch_size, sequence_length=sequence_length),
        "tied_weights": {
            "lm_head.weight": "token_embedding.weight",
            "is_tied": output_head_is_tied(model),
            "note": "The output projection reuses token_embedding.weight, so it is not counted twice.",
        },
        "checkpoint": checkpoint_metadata or {},
    }
    report["parameter_check"] = {
        "owned_sum_matches_total": owned_parameters == total_parameters,
        "difference": owned_parameters - total_parameters,
    }
    return report


def write_model_report_svg(report: dict[str, Any], path: str | Path) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    config = report["config"]
    groups = report["owned_parameter_groups"]
    total_parameters = int(report["total_parameters"])
    max_group = max((int(group["parameters"]) for group in groups), default=1)

    width = 980
    top = 94
    box_y = top
    box_h = 58
    gap = 18
    boxes = [
        ("Token ids", "B x T"),
        ("Embeddings", f"T x {config['n_embd']}"),
        ("Blocks", f"{config['n_layer']} x attention + MLP"),
        ("LayerNorm", f"{config['n_embd']}"),
        ("Logits", f"T x {config['vocab_size']}"),
    ]

    box_w = int((width - 56 - gap * (len(boxes) - 1)) / len(boxes))
    box_rows: list[str] = []
    for i, (title, subtitle) in enumerate(boxes):
        x = 28 + i * (box_w + gap)
        box_rows.append(f'<rect x="{x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="6" fill="#eef2ff" stroke="#4f46e5"/>')
        box_rows.append(
            f'<text x="{x + 12}" y="{box_y + 24}" font-family="Arial" font-size="14" fill="#111827">'
            f'{html.escape(title)}</text>'
        )
        box_rows.append(
            f'<text x="{x + 12}" y="{box_y + 46}" font-family="Arial" font-size="12" fill="#374151">'
            f'{html.escape(subtitle)}</text>'
        )
        if i < len(boxes) - 1:
            ax = x + box_w + 4
            ay = box_y + box_h // 2
            box_rows.append(f'<line x1="{ax}" y1="{ay}" x2="{ax + gap - 8}" y2="{ay}" stroke="#111827" stroke-width="2"/>')
            box_rows.append(f'<polygon points="{ax + gap - 8},{ay - 5} {ax + gap - 8},{ay + 5} {ax + gap},{ay}" fill="#111827"/>')

    bars: list[str] = []
    bar_top = box_y + box_h + 70
    bar_left = 230
    bar_width = 620
    row_h = 36
    for i, group in enumerate(groups):
        y = bar_top + i * row_h
        params = int(group["parameters"])
        bar = max(2, int(bar_width * params / max_group))
        label = f"{group['label']} ({group['percent']}%)"
        bars.append(f'<text x="28" y="{y + 22}" font-family="Arial" font-size="14" fill="#111827">{html.escape(label)}</text>')
        bars.append(f'<rect x="{bar_left}" y="{y + 7}" width="{bar}" height="22" rx="3" fill="#2563eb"/>')
        bars.append(f'<text x="{bar_left + bar + 10}" y="{y + 22}" font-family="Arial" font-size="13" fill="#374151">{params:,}</text>')

    height = bar_top + row_h * len(groups) + 62
    tied_note = "lm_head.weight is tied to token_embedding.weight"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="28" y="34" font-family="Arial" font-size="20" fill="#111827">MiniGPT model report</text>
  <text x="28" y="60" font-family="Arial" font-size="13" fill="#374151">layers={config['n_layer']} heads={config['n_head']} embd={config['n_embd']} block={config['block_size']} vocab={config['vocab_size']} params={total_parameters:,}</text>
  {''.join(box_rows)}
  <text x="28" y="{bar_top - 24}" font-family="Arial" font-size="16" fill="#111827">Owned parameter groups</text>
  {''.join(bars)}
  <text x="28" y="{height - 24}" font-family="Arial" font-size="13" fill="#374151">{html.escape(tied_note)}</text>
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")
