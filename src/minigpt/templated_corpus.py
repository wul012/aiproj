"""A larger, structured synthetic Chinese corpus with a true held-out split.

The v1156 LoRA run could only report training loss honestly because the bundled
``data/sample_zh.txt`` is 507 characters — far too small for a meaningful
validation signal. This module builds a deterministic, templated corpus where
sentences are generated from a small grammar over a shared vocabulary, then
split *by sentence* into train and held-out halves.

Because train and held-out sentences share the same grammar and vocabulary but
are disjoint combinations, held-out loss/accuracy measures genuine
generalization (predicting unseen-but-in-distribution sequences) rather than
memorization. The corpus is synthetic, not natural text — natural-text scale is
a later step — but it gives a reproducible, real generalization signal today.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# A small grammar. Each axis shares characters across many sentences, so held-out
# sentences stay in-distribution at the character level.
TIMES = ["清晨", "上午", "正午", "傍晚", "深夜", "周末", "雨天", "假期"]
SUBJECTS = ["工程师", "学生", "老师", "画家", "医生", "船长", "农夫", "旅人"]
VERBS = ["修好了", "记录了", "讲解了", "测量了", "整理了", "发现了", "保存了", "比较了"]
OBJECTS = ["模型", "数据", "地图", "故事", "图纸", "样本", "账本", "信号"]


@dataclass
class TemplatedCorpus:
    """A train/held-out split built from a shared grammar."""

    train_text: str
    heldout_text: str
    train_sentences: list[str] = field(default_factory=list)
    heldout_sentences: list[str] = field(default_factory=list)
    seed: int = 0
    heldout_ratio: float = 0.2

    @property
    def full_text(self) -> str:
        return self.train_text + self.heldout_text

    def stats(self) -> dict[str, int | float]:
        return {
            "train_sentence_count": len(self.train_sentences),
            "heldout_sentence_count": len(self.heldout_sentences),
            "train_char_count": len(self.train_text),
            "heldout_char_count": len(self.heldout_text),
            "vocab_char_count": len(set(self.full_text)),
        }


def _all_sentences() -> list[str]:
    sentences: list[str] = []
    for time in TIMES:
        for subject in SUBJECTS:
            for verb in VERBS:
                for obj in OBJECTS:
                    sentences.append(f"{time}，{subject}{verb}{obj}。")
    return sentences


def build_templated_corpus(
    *,
    seed: int = 1337,
    heldout_ratio: float = 0.2,
    max_sentences: int | None = 400,
) -> TemplatedCorpus:
    """Build a deterministic templated corpus split by sentence.

    The same ``seed`` always yields the same train/held-out split, so the corpus
    is reproducible across runs and tests.
    """
    if not 0.0 < heldout_ratio < 1.0:
        raise ValueError("heldout_ratio must be between 0 and 1")

    sentences = _all_sentences()
    rng = random.Random(seed)
    rng.shuffle(sentences)
    if max_sentences is not None:
        if max_sentences < 2:
            raise ValueError("max_sentences must be at least 2")
        sentences = sentences[:max_sentences]

    n_heldout = max(1, int(len(sentences) * heldout_ratio))
    if n_heldout >= len(sentences):
        raise ValueError("heldout split would consume every sentence; lower heldout_ratio")
    heldout_sentences = sentences[:n_heldout]
    train_sentences = sentences[n_heldout:]

    return TemplatedCorpus(
        train_text="".join(train_sentences),
        heldout_text="".join(heldout_sentences),
        train_sentences=train_sentences,
        heldout_sentences=heldout_sentences,
        seed=seed,
        heldout_ratio=heldout_ratio,
    )


__all__ = ["TemplatedCorpus", "build_templated_corpus"]
