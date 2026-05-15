from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from minigpt.server_contracts import GenerationRequest, GenerationResponse, GenerationStreamChunk


class MiniGPTGenerator:
    def __init__(
        self,
        checkpoint_path: str | Path,
        tokenizer_path: str | Path | None = None,
        device: str = "auto",
    ) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.tokenizer_path = Path(tokenizer_path) if tokenizer_path is not None else self.checkpoint_path.parent / "tokenizer.json"
        self.device_name = device
        self._loaded: tuple[Any, Any, Any] | None = None

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        torch, model, tokenizer = self._load()
        prompt_ids = tokenizer.encode(request.prompt)
        if not prompt_ids:
            raise ValueError("prompt produced no token ids")
        if len(prompt_ids) > model.config.block_size:
            prompt_ids = prompt_ids[-model.config.block_size :]
        if request.seed is not None:
            torch.manual_seed(request.seed)
            if self._device(torch).type == "cuda":
                torch.cuda.manual_seed_all(request.seed)

        idx = torch.tensor([prompt_ids], dtype=torch.long, device=self._device(torch))
        with torch.no_grad():
            out = model.generate(
                idx,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
                top_k=request.top_k,
            )
        generated = tokenizer.decode(out[0].tolist())
        continuation = generated[len(request.prompt) :] if generated.startswith(request.prompt) else generated
        return GenerationResponse(
            prompt=request.prompt,
            generated=generated,
            continuation=continuation,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_k=request.top_k,
            seed=request.seed,
            checkpoint=str(self.checkpoint_path),
            tokenizer=getattr(tokenizer, "name", "unknown"),
        )

    def stream(self, request: GenerationRequest) -> Iterator[GenerationStreamChunk]:
        torch, model, tokenizer = self._load()
        prompt_ids = tokenizer.encode(request.prompt)
        if not prompt_ids:
            raise ValueError("prompt produced no token ids")
        if len(prompt_ids) > model.config.block_size:
            prompt_ids = prompt_ids[-model.config.block_size :]
        if request.seed is not None:
            torch.manual_seed(request.seed)
            if self._device(torch).type == "cuda":
                torch.cuda.manual_seed_all(request.seed)

        idx = torch.tensor([prompt_ids], dtype=torch.long, device=self._device(torch))
        for index in range(request.max_new_tokens):
            next_idx = model.sample_next(idx, temperature=request.temperature, top_k=request.top_k)
            idx = torch.cat((idx, next_idx), dim=1)
            token_id = int(next_idx[0, 0].item())
            generated = tokenizer.decode(idx[0].tolist())
            continuation = generated[len(request.prompt) :] if generated.startswith(request.prompt) else generated
            yield GenerationStreamChunk(
                index=index,
                token_id=token_id,
                text=tokenizer.decode([token_id]),
                generated=generated,
                continuation=continuation,
                checkpoint=str(self.checkpoint_path),
                tokenizer=getattr(tokenizer, "name", "unknown"),
            )

    def _load(self) -> tuple[Any, Any, Any]:
        if self._loaded is not None:
            return self._loaded

        import torch

        from .model import GPTConfig, MiniGPT
        from .tokenizer import load_tokenizer

        device = self._device(torch)
        checkpoint = torch.load(self.checkpoint_path, map_location=device, weights_only=False)
        tokenizer = load_tokenizer(self.tokenizer_path)
        config = GPTConfig(**checkpoint["config"])
        model = MiniGPT(config).to(device)
        model.load_state_dict(checkpoint["model"])
        model.eval()
        self._loaded = (torch, model, tokenizer)
        return self._loaded

    def _device(self, torch: Any) -> Any:
        if self.device_name == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.device_name == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
        return torch.device(self.device_name)
