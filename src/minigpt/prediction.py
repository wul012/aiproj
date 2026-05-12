from __future__ import annotations

import html
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch.nn import functional as F


@dataclass(frozen=True)
class TokenPrediction:
    rank: int
    token_id: int
    token: str
    probability: float
    logit: float

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def top_k_predictions(
    logits: torch.Tensor,
    tokens: list[str],
    k: int = 10,
    temperature: float = 1.0,
) -> list[TokenPrediction]:
    if logits.ndim != 1:
        raise ValueError("logits must be a 1D tensor")
    if k < 1:
        raise ValueError("k must be at least 1")
    if temperature <= 0:
        raise ValueError("temperature must be greater than 0")

    scaled = logits.detach().float() / temperature
    probs = F.softmax(scaled, dim=-1)
    top_probs, top_ids = torch.topk(probs, min(k, probs.numel()))

    predictions: list[TokenPrediction] = []
    for rank, (prob, token_id) in enumerate(zip(top_probs.tolist(), top_ids.tolist()), start=1):
        token = tokens[token_id] if token_id < len(tokens) else f"<id:{token_id}>"
        predictions.append(
            TokenPrediction(
                rank=rank,
                token_id=int(token_id),
                token=token,
                probability=round(float(prob), 8),
                logit=round(float(logits[token_id]), 8),
            )
        )
    return predictions


def perplexity_from_loss(loss: float) -> float:
    if loss > 100:
        return math.inf
    return float(math.exp(loss))


def token_label(token: str, limit: int = 18) -> str:
    label = token.replace("\n", "\\n").replace("\t", "\\t")
    if len(label) > limit:
        return label[: limit - 1] + "…"
    return label


def write_predictions_svg(predictions: list[TokenPrediction], path: str | Path, title: str = "MiniGPT next-token predictions") -> None:
    if not predictions:
        raise ValueError("Cannot write predictions SVG without predictions")

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    width = 860
    row_height = 34
    top = 72
    left = 170
    bar_width = 560
    height = top + row_height * len(predictions) + 44
    max_prob = max(prediction.probability for prediction in predictions) or 1.0

    rows: list[str] = []
    for i, prediction in enumerate(predictions):
        y = top + i * row_height
        label = html.escape(token_label(prediction.token))
        prob = prediction.probability
        bar = max(2, int(bar_width * prob / max_prob))
        rows.append(
            f'<text x="28" y="{y + 22}" font-family="Arial" font-size="14" fill="#111827">'
            f'{prediction.rank}. {label}</text>'
        )
        rows.append(f'<rect x="{left}" y="{y + 5}" width="{bar}" height="22" rx="3" fill="#2563eb"/>')
        rows.append(
            f'<text x="{left + bar + 10}" y="{y + 22}" font-family="Arial" font-size="13" fill="#374151">'
            f'{prob:.4f}</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#fbfbf7"/>
  <text x="28" y="32" font-family="Arial" font-size="18" fill="#111827">{html.escape(title)}</text>
  <text x="28" y="54" font-family="Arial" font-size="13" fill="#374151">Higher bar means higher next-token probability.</text>
  {''.join(rows)}
</svg>
"""
    out_path.write_text(svg, encoding="utf-8")
