from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from minigpt.dataset import get_batch, load_text, split_token_ids
from minigpt.data_prep import build_dataset_report, build_prepared_dataset, write_dataset_report_json, write_dataset_report_svg
from minigpt.data_quality import build_dataset_quality_report, write_dataset_quality_json, write_dataset_quality_svg
from minigpt.history import TrainingRecord, append_record, load_records, summarize_records, write_loss_curve_svg
from minigpt.manifest import build_environment_metadata, build_run_manifest, utc_now, write_run_manifest_json, write_run_manifest_svg
from minigpt.model import GPTConfig, MiniGPT
from minigpt.tokenizer import BPETokenizer, CharTokenizer, Tokenizer, load_tokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a tiny GPT language model.")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "sample_zh.txt")
    parser.add_argument("--data-dir", type=Path, default=None, help="Directory of .txt files to merge for training")
    parser.add_argument("--prepared-data", type=Path, default=None, help="Prepared corpus text file from prepare_dataset.py")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs" / "minigpt")
    parser.add_argument("--resume", type=Path, default=None, help="Resume from a previous checkpoint.pt")
    parser.add_argument("--tokenizer", choices=["char", "bpe"], default="char")
    parser.add_argument("--bpe-vocab-size", type=int, default=256)
    parser.add_argument("--bpe-min-frequency", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=128)
    parser.add_argument("--max-iters", type=int, default=1000)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--train-ratio", type=float, default=0.9)
    parser.add_argument("--n-layer", type=int, default=4)
    parser.add_argument("--n-head", type=int, default=4)
    parser.add_argument("--n-embd", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--sample-prompt", type=str, default="人工智能")
    parser.add_argument("--sample-tokens", type=int, default=80)
    parser.add_argument("--sample-temperature", type=float, default=0.8)
    parser.add_argument("--sample-top-k", type=int, default=30)
    parser.add_argument("--no-sample", action="store_true")
    return parser.parse_args()


def choose_device(name: str) -> torch.device:
    if name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False")
    return torch.device(name)


@torch.no_grad()
def estimate_loss(
    model: MiniGPT,
    train_data: torch.Tensor,
    val_data: torch.Tensor,
    block_size: int,
    batch_size: int,
    eval_iters: int,
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    out: dict[str, float] = {}
    for split, data in [("train", train_data), ("val", val_data)]:
        losses = torch.empty(eval_iters)
        for k in range(eval_iters):
            x, y = get_batch(data, block_size, batch_size, device)
            _, loss = model(x, y)
            if loss is None:
                raise RuntimeError("Expected a loss during evaluation")
            losses[k] = loss.item()
        out[split] = float(losses.mean())
    model.train()
    return out


def load_resume_state(resume_path: Path, device: torch.device) -> tuple[dict, Tokenizer, GPTConfig]:
    checkpoint = torch.load(resume_path, map_location=device, weights_only=False)
    tokenizer_path = resume_path.parent / "tokenizer.json"
    if not tokenizer_path.exists():
        raise FileNotFoundError(f"Resume tokenizer not found: {tokenizer_path}")
    tokenizer = load_tokenizer(tokenizer_path)
    config = GPTConfig(**checkpoint["config"])
    if config.vocab_size != tokenizer.vocab_size:
        raise ValueError(
            f"Checkpoint vocab_size={config.vocab_size}, but tokenizer vocab_size={tokenizer.vocab_size}"
        )
    return checkpoint, tokenizer, config


def train_tokenizer(args: argparse.Namespace, text: str) -> Tokenizer:
    if args.tokenizer == "bpe":
        return BPETokenizer.train(
            text,
            vocab_size=args.bpe_vocab_size,
            min_frequency=args.bpe_min_frequency,
        )
    return CharTokenizer.train(text)


def load_training_text(args: argparse.Namespace) -> tuple[str, dict[str, object], object | None]:
    provided = [args.data_dir is not None, args.prepared_data is not None]
    if sum(provided) > 1:
        raise ValueError("Use only one of --data-dir or --prepared-data")
    if args.prepared_data is not None:
        text = load_text(args.prepared_data)
        return text, {"kind": "prepared_data", "path": str(args.prepared_data)}, None
    if args.data_dir is not None:
        dataset = build_prepared_dataset([args.data_dir], recursive=True)
        return text_or_raise(dataset.text, args.data_dir), {
            "kind": "data_dir",
            "path": str(args.data_dir),
            "source_count": len(dataset.sources),
        }, dataset
    text = load_text(args.data)
    return text, {"kind": "data", "path": str(args.data)}, None


def text_or_raise(text: str, source: Path) -> str:
    if not text.strip():
        raise ValueError(f"Training data is empty: {source}")
    return text


def copy_prepared_artifacts(prepared_data: Path, out_dir: Path) -> None:
    prepared_copy = out_dir / "prepared_corpus.txt"
    if prepared_data.resolve() != prepared_copy.resolve():
        shutil.copyfile(prepared_data, prepared_copy)

    for artifact_name in ("dataset_report.json", "dataset_report.svg", "dataset_quality.json", "dataset_quality.svg"):
        artifact_path = prepared_data.parent / artifact_name
        if artifact_path.exists():
            shutil.copyfile(artifact_path, out_dir / artifact_name)


@torch.no_grad()
def write_sample(
    model: MiniGPT,
    tokenizer: Tokenizer,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_k: int,
    device: torch.device,
    out_path: Path,
) -> None:
    model.eval()
    prompt_ids = tokenizer.encode(prompt)
    idx = torch.tensor([prompt_ids], dtype=torch.long, device=device)
    out = model.generate(
        idx,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_k=top_k,
    )
    generated = tokenizer.decode(out[0].tolist())
    out_path.write_text(
        "\n".join(
            [
                f"prompt: {prompt}",
                f"max_new_tokens: {max_new_tokens}",
                f"temperature: {temperature}",
                f"top_k: {top_k}",
                "",
                generated,
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    started_at = utc_now()
    default_out_dir = ROOT / "runs" / "minigpt"
    if args.resume is not None and args.out_dir == default_out_dir:
        args.out_dir = args.resume.parent

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    random.seed(args.seed)

    device = choose_device(args.device)
    text, data_source, prepared_dataset = load_training_text(args)

    checkpoint = None
    resume_step = 0
    if args.resume is not None:
        checkpoint, tokenizer, config = load_resume_state(args.resume, device)
        resume_step = int(checkpoint.get("step", 0))
    else:
        tokenizer = train_tokenizer(args, text)
        config = GPTConfig(
            vocab_size=tokenizer.vocab_size,
            block_size=args.block_size,
            n_layer=args.n_layer,
            n_head=args.n_head,
            n_embd=args.n_embd,
            dropout=args.dropout,
        )

    token_ids = tokenizer.encode(text)
    train_data, val_data = split_token_ids(token_ids, train_ratio=args.train_ratio)

    model = MiniGPT(config).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    if checkpoint is not None:
        model.load_state_dict(checkpoint["model"])
        if "optimizer" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer"])

    start_step = resume_step + 1
    if args.max_iters < start_step:
        raise ValueError(
            f"--max-iters={args.max_iters} is before the next resume step {start_step}. "
            "Use a larger --max-iters target."
        )

    print(f"device={device}")
    print(f"tokenizer={getattr(tokenizer, 'name', 'unknown')}")
    print(f"tokens={len(token_ids)} vocab_size={tokenizer.vocab_size}")
    print(f"parameters={model.parameter_count():,}")
    print(f"data_source={data_source['kind']}:{data_source['path']}")
    if args.resume is not None:
        print(f"resume={args.resume} resume_step={resume_step} target_step={args.max_iters}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if prepared_dataset is not None:
        prepared_path = args.out_dir / "prepared_corpus.txt"
        prepared_path.write_text(prepared_dataset.text, encoding="utf-8")
        report = build_dataset_report(prepared_dataset, output_text=prepared_path)
        write_dataset_report_json(report, args.out_dir / "dataset_report.json")
        write_dataset_report_svg(report, args.out_dir / "dataset_report.svg")
        quality = build_dataset_quality_report(prepared_dataset)
        write_dataset_quality_json(quality, args.out_dir / "dataset_quality.json")
        write_dataset_quality_svg(quality, args.out_dir / "dataset_quality.svg")
    elif args.prepared_data is not None:
        copy_prepared_artifacts(args.prepared_data, args.out_dir)
    history_path = args.out_dir / "metrics.jsonl"
    if args.resume is None and history_path.exists():
        history_path.unlink()

    last_loss = None
    for step in range(start_step, args.max_iters + 1):
        x, y = get_batch(train_data, config.block_size, args.batch_size, device)
        _, loss = model(x, y)
        if loss is None:
            raise RuntimeError("Expected a loss during training")

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        last_loss = float(loss.item())

        if step == 1 or step % args.eval_interval == 0 or step == args.max_iters:
            losses = estimate_loss(
                model=model,
                train_data=train_data,
                val_data=val_data,
                block_size=config.block_size,
                batch_size=args.batch_size,
                eval_iters=args.eval_iters,
                device=device,
            )
            print(f"step={step:5d} train_loss={losses['train']:.4f} val_loss={losses['val']:.4f}")
            append_record(
                history_path,
                TrainingRecord(
                    step=step,
                    train_loss=losses["train"],
                    val_loss=losses["val"],
                    last_loss=last_loss,
                ),
            )

    history_summary = None
    records = load_records(history_path)
    if records:
        write_loss_curve_svg(records, args.out_dir / "loss_curve.svg")
        history_summary = summarize_records(records)
        (args.out_dir / "history_summary.json").write_text(
            json.dumps(history_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if not args.no_sample:
        write_sample(
            model=model,
            tokenizer=tokenizer,
            prompt=args.sample_prompt,
            max_new_tokens=args.sample_tokens,
            temperature=args.sample_temperature,
            top_k=args.sample_top_k,
            device=device,
            out_path=args.out_dir / "sample.txt",
        )

    checkpoint = {
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "config": asdict(config),
        "last_loss": last_loss,
        "step": args.max_iters,
        "history_file": "metrics.jsonl",
        "sample_file": None if args.no_sample else "sample.txt",
        "tokenizer_type": getattr(tokenizer, "name", "unknown"),
        "data_source": data_source,
    }
    torch.save(checkpoint, args.out_dir / "checkpoint.pt")
    tokenizer.save(args.out_dir / "tokenizer.json")
    train_config = vars(args) | {"device_used": str(device), "data_source": data_source}
    (args.out_dir / "train_config.json").write_text(
        json.dumps(train_config, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    finished_at = utc_now()
    manifest = build_run_manifest(
        args.out_dir,
        args=train_config,
        data_source=data_source,
        model_config=asdict(config),
        tokenizer_name=getattr(tokenizer, "name", "unknown"),
        token_count=len(token_ids),
        train_token_count=len(train_data),
        val_token_count=len(val_data),
        parameter_count=model.parameter_count(),
        device_used=str(device),
        started_at=started_at,
        finished_at=finished_at,
        start_step=start_step,
        end_step=args.max_iters,
        last_loss=last_loss,
        history_summary=history_summary,
        command=[Path(sys.executable).name, *sys.argv],
        repo_root=ROOT,
        environment=build_environment_metadata({"torch": torch.__version__, "numpy": np.__version__}),
    )
    write_run_manifest_json(manifest, args.out_dir / "run_manifest.json")
    write_run_manifest_svg(manifest, args.out_dir / "run_manifest.svg")
    print(f"saved={args.out_dir}")
    print(f"history={history_path}")
    print(f"manifest={args.out_dir / 'run_manifest.json'}")
    if not args.no_sample:
        print(f"sample={args.out_dir / 'sample.txt'}")


if __name__ == "__main__":
    main()
