from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


DEFAULT_GENERATION_PROFILE_ID = "default"
NEWLINE_SUPPRESSION_PROFILE_ID = "suppress_newline_tokens"


@dataclass(frozen=True)
class GenerationProfile:
    id: str
    label: str
    description: str
    blocked_token_texts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


GENERATION_PROFILES: tuple[GenerationProfile, ...] = (
    GenerationProfile(
        DEFAULT_GENERATION_PROFILE_ID,
        "Default",
        "Use the model's normal decoding path.",
    ),
    GenerationProfile(
        NEWLINE_SUPPRESSION_PROFILE_ID,
        "Suppress newline tokens",
        "Block tokenizer entries containing newline separators during decoding.",
        ("\n", "\r"),
    ),
)


def generation_profile_options() -> list[dict[str, Any]]:
    return [profile.to_dict() for profile in GENERATION_PROFILES]


def build_generation_profiles_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "default_generation_profile_id": DEFAULT_GENERATION_PROFILE_ID,
        "profile_count": len(GENERATION_PROFILES),
        "profiles": generation_profile_options(),
    }


def generation_profile_ids() -> tuple[str, ...]:
    return tuple(profile.id for profile in GENERATION_PROFILES)


def normalize_generation_profile(profile_id: Any) -> str:
    if profile_id is None:
        return DEFAULT_GENERATION_PROFILE_ID
    text = str(profile_id).strip()
    return text or DEFAULT_GENERATION_PROFILE_ID


def resolve_generation_profile(profile_id: Any) -> GenerationProfile:
    normalized = normalize_generation_profile(profile_id)
    for profile in GENERATION_PROFILES:
        if profile.id == normalized:
            return profile
    raise ValueError(f"unknown generation_profile: {normalized}")


def blocked_token_texts_for_profile(profile_id: Any) -> tuple[str, ...]:
    return resolve_generation_profile(profile_id).blocked_token_texts


def merge_blocked_token_texts(profile_id: Any, explicit_texts: tuple[str, ...]) -> tuple[str, ...]:
    merged: list[str] = []
    for text in blocked_token_texts_for_profile(profile_id) + explicit_texts:
        if text and text not in merged:
            merged.append(text)
    return tuple(merged)
