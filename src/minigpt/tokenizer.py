from __future__ import annotations

from collections import Counter
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CharTokenizer:
    """A tiny character-level tokenizer for learning language modeling."""

    stoi: dict[str, int]
    itos: list[str]
    unk_token: str = "<unk>"
    name: str = "char"

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
            "type": self.name,
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


@dataclass
class BPETokenizer:
    """A small character-seeded BPE tokenizer for understanding subword merging."""

    stoi: dict[str, int]
    itos: list[str]
    merges: list[tuple[str, str]]
    unk_token: str = "<unk>"
    name: str = "bpe"

    @classmethod
    def train(
        cls,
        text: str,
        vocab_size: int = 256,
        min_frequency: int = 2,
        unk_token: str = "<unk>",
    ) -> "BPETokenizer":
        if vocab_size < 2:
            raise ValueError("vocab_size must be at least 2")
        if min_frequency < 1:
            raise ValueError("min_frequency must be at least 1")

        chars = sorted(set(text))
        vocab = [unk_token] + [ch for ch in chars if ch != unk_token]
        sequences = [list(text)]
        merges: list[tuple[str, str]] = []

        while len(vocab) < vocab_size:
            pair_counts = _count_pairs(sequences)
            if not pair_counts:
                break

            best_pair, best_count = min(
                pair_counts.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )
            if best_count < min_frequency:
                break

            merged = "".join(best_pair)
            if merged in vocab:
                break
            sequences = [_merge_pair(sequence, best_pair, merged) for sequence in sequences]
            merges.append(best_pair)
            vocab.append(merged)

        return cls(stoi={token: i for i, token in enumerate(vocab)}, itos=vocab, merges=merges, unk_token=unk_token)

    @property
    def vocab_size(self) -> int:
        return len(self.itos)

    def encode(self, text: str) -> list[int]:
        tokens = list(text)
        for left, right in self.merges:
            tokens = _merge_pair(tokens, (left, right), left + right)
        unk_id = self.stoi[self.unk_token]
        return [self.stoi.get(token, unk_id) for token in tokens]

    def decode(self, ids: list[int]) -> str:
        pieces: list[str] = []
        for idx in ids:
            token = self.itos[int(idx)]
            pieces.append("�" if token == self.unk_token else token)
        return "".join(pieces)

    def save(self, path: str | Path) -> None:
        payload = {
            "type": self.name,
            "itos": self.itos,
            "merges": [[left, right] for left, right in self.merges],
            "unk_token": self.unk_token,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "BPETokenizer":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        itos = list(payload["itos"])
        merges = [tuple(pair) for pair in payload.get("merges", [])]
        return cls(
            stoi={token: i for i, token in enumerate(itos)},
            itos=itos,
            merges=[(str(left), str(right)) for left, right in merges],
            unk_token=payload.get("unk_token", "<unk>"),
        )


Tokenizer = CharTokenizer | BPETokenizer


def load_tokenizer(path: str | Path) -> Tokenizer:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    tokenizer_type = payload.get("type")
    if tokenizer_type == "bpe" or "merges" in payload:
        return BPETokenizer.load(path)
    return CharTokenizer.load(path)


def _count_pairs(sequences: list[list[str]]) -> Counter[tuple[str, str]]:
    pair_counts: Counter[tuple[str, str]] = Counter()
    for sequence in sequences:
        pair_counts.update(zip(sequence, sequence[1:]))
    return pair_counts


def _merge_pair(sequence: list[str], pair: tuple[str, str], merged: str) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(sequence):
        if i + 1 < len(sequence) and sequence[i] == pair[0] and sequence[i + 1] == pair[1]:
            out.append(merged)
            i += 2
        else:
            out.append(sequence[i])
            i += 1
    return out
