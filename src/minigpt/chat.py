from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


ROLE_LABELS = {
    "system": "系统",
    "user": "用户",
    "assistant": "助手",
}
DEFAULT_STOP_MARKERS = ("\n用户：", "\n系统：", "\n助手：")


class EncodableTokenizer(Protocol):
    def encode(self, text: str) -> list[int]:
        ...

    def decode(self, ids: list[int]) -> str:
        ...


@dataclass(frozen=True)
class ChatTurn:
    role: str
    content: str

    def __post_init__(self) -> None:
        normalized = self.role.strip().lower()
        if normalized not in ROLE_LABELS:
            raise ValueError(f"Unsupported chat role: {self.role}")
        if not self.content.strip():
            raise ValueError("Chat turn content cannot be empty")
        object.__setattr__(self, "role", normalized)
        object.__setattr__(self, "content", self.content.strip())

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PreparedChatPrompt:
    text: str
    decoded_context: str
    token_ids: list[int]
    original_token_count: int
    trimmed: bool


def build_chat_prompt(
    turns: list[ChatTurn],
    system_prompt: str | None = None,
    add_assistant_prompt: bool = True,
) -> str:
    lines: list[str] = []
    if system_prompt is not None and system_prompt.strip():
        lines.extend([f"{ROLE_LABELS['system']}：{system_prompt.strip()}", ""])

    for turn in turns:
        lines.extend([f"{ROLE_LABELS[turn.role]}：{turn.content}", ""])

    if add_assistant_prompt:
        lines.append(f"{ROLE_LABELS['assistant']}：")
    elif lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def prepare_chat_prompt(
    tokenizer: EncodableTokenizer,
    prompt: str,
    block_size: int,
) -> PreparedChatPrompt:
    if block_size < 1:
        raise ValueError("block_size must be at least 1")

    token_ids = tokenizer.encode(prompt)
    if not token_ids:
        raise ValueError("Prompt produced no token ids")

    original_token_count = len(token_ids)
    trimmed = original_token_count > block_size
    if trimmed:
        token_ids = token_ids[-block_size:]

    return PreparedChatPrompt(
        text=prompt,
        decoded_context=tokenizer.decode(token_ids),
        token_ids=token_ids,
        original_token_count=original_token_count,
        trimmed=trimmed,
    )


def stop_at_markers(text: str, markers: tuple[str, ...] = DEFAULT_STOP_MARKERS) -> str:
    stop_positions = [text.find(marker) for marker in markers if marker and text.find(marker) >= 0]
    if not stop_positions:
        return text.strip()
    return text[: min(stop_positions)].strip()


def assistant_reply_from_generation(
    generated_text: str,
    decoded_context: str,
    markers: tuple[str, ...] = DEFAULT_STOP_MARKERS,
) -> str:
    if generated_text.startswith(decoded_context):
        generated_text = generated_text[len(decoded_context) :]
    return stop_at_markers(generated_text, markers=markers)


def turns_to_dicts(turns: list[ChatTurn]) -> list[dict[str, str]]:
    return [turn.to_dict() for turn in turns]
