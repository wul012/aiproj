from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CharTokenizer:
    """A tiny character-level tokenizer for learning language modeling."""

    stoi: dict[str, int]
    itos: list[str]
    unk_token: str = "<unk>"

    @classmethod
    def train(cls, text: str, unk_token: str = "<unk>") -> "CharTokenizer":
        chars = sorted(set(text))
        vocab = [unk_token] + [ch for ch in chars if ch != unk_token]
        return cls(stoi={ch: i for i, ch in enumerate(vocab)}, itos=vocab, unk_token=unk_token)

    @property
    def vocab_size(self) -> int:
        return len(self.itos)

    def encode(self, text: str) -> list[int]:
        unk_id = self.stoi[self.unk_token]
        return [self.stoi.get(ch, unk_id) for ch in text]

    def decode(self, ids: list[int]) -> str:
        pieces: list[str] = []
        for idx in ids:
            token = self.itos[int(idx)]
            pieces.append("�" if token == self.unk_token else token)
        return "".join(pieces)

    def save(self, path: str | Path) -> None:
        payload = {
            "itos": self.itos,
            "unk_token": self.unk_token,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "CharTokenizer":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        itos = list(payload["itos"])
        return cls(
            stoi={ch: i for i, ch in enumerate(itos)},
            itos=itos,
            unk_token=payload.get("unk_token", "<unk>"),
        )
