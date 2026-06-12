# v1154 unassisted loss suffix repair training run 代码讲解

## 本版目标与边界

v1154 是 v1153 之后的下一步 bounded training。它唯一要做的事情，就是把已经在 v1153 里修订好的 loss-suffix seed corpus 送进训练脚本，产出 checkpoint、metrics、manifest、history summary、loss curve、sample 和 handoff。它不负责 replay，不负责评估恢复，也不负责 promotion。它只证明一件事：修订后的语料确实被训练流程完整吃进去了，且训练指标在一个可控的小模型上确实下降了。

这个边界必须明确，因为在这种短版本链里最容易发生的误解就是：训练 loss 下降了，就直接说模型能力提升了。v1154 不做这种跳跃。它只提供训练侧证据，和 v1153 一样，仍然保持 `model_quality_claim=training_artifact_only`。

## 输入和前置产物

v1154 的输入有两个，但本质上是同一份材料的两个视角：`f/1153/.../unassisted_loss_suffix_repair_seed_v1153.json` 和它导出的 `unassisted_loss_suffix_repair_seed_corpus_v1153.txt`。前者是结构化报告，告诉训练脚本这份 corpus 为什么存在、包含多少 base rows、多少 repair rows、多少 target-free holdout prompts；后者是训练脚本真正吃进去的纯文本。

在实现上，`build_unassisted_loss_suffix_repair_training_run_v1154()` 会重新读 `prepared_corpus.txt`、`metrics.jsonl`、`train_config.json`、`run_manifest.json` 和 `sample.txt`。这套读取方式和 v1150 的训练版是同一条风格线：训练证据不能只靠某个 wrapper 的返回值，必须回到 run 目录里的真实文件。这也是为什么本版仍然保留 `artifact_rows`、`metrics`、`train_config` 和 `manifest` 四块独立结构。

## 核心模块结构

### 1. 路径解析

`default_v1153_seed_corpus_path()` 和 `locate_v1153_seed_corpus()` 负责把 `f/1153` 归档目录和命令行输入统一起来。前者给 CLI 一个默认入口，后者让用户既能传 JSON 文件，也能传整个输出目录。`seed_corpus_text_path()` 则把 seed corpus JSON 的同级 `.txt` 路径算出来，方便 `--run-training` 时把真正的 prepared data 交给 `scripts/train.py`。

### 2. 训练证据构造

`build_unassisted_loss_suffix_repair_training_run_v1154()` 是主入口。它读到 run 目录后，先构造 `artifact_rows`，再读取 `metrics.jsonl`、`train_config.json`、`run_manifest.json` 和 `prepared_corpus.txt`，最后跑 `_checks()`。这一层主要负责验证训练产物是否齐全，以及训练是不是确实使用了 v1153 的 corpus。

`_checks()` 是本版最重要的 contract gate。它至少检查以下几件事：

- 上游 v1153 seed corpus 是否 pass
- 上游 v1153 summary 的 ready flag 是否 true
- v1153 的 next step 是否确实指向 bounded training
- checkpoint、tokenizer、metrics、manifest 是否存在
- `prepared_corpus.txt` 是否与 v1153 的 `corpus_text` 完全一致
- metrics 是否至少有 first 和 last 两条记录
- 最后一条 step 是否真的跑到 `max_iters`
- train / val loss 是否都下降
- training artifact 是否仍然保持 promotion boundary

这意味着 v1154 不是简单看“跑完了没有”，而是把训练是否真的吃到修订语料、是否真的完成了 bounded 训练、是否真的保留了非 promotion 边界，一起锁死。

### 3. training_run 结构

`_training()` 把训练侧的结果压成一个小对象，里面有 `final_step`、`final_train_loss`、`final_val_loss`、`train_loss_delta`、`val_loss_delta`、`sample_fixed_hit`、`sample_loss_hit` 和 `proposed_next_artifact`。这里面最值得注意的是 `sample_loss_hit=True`。这说明 sample 已经不再只是命中 fixed，而是出现了 loss 词面，和 v1152 的诊断方向一致。

但是这个字段不能被误读成能力恢复。原因有两个。第一，sample 只是训练过程里的一个抽样输出，不是固定 holdout。第二，本版的 `interpretation` 仍然明确写着 `training_artifact_only`。所以 `sample_loss_hit=True` 只是“训练侧有了更强的局部信号”，不是“holdout 已恢复”。

## 训练命令和运行方式

`scripts/run_unassisted_loss_suffix_repair_training_v1154.py` 提供了完整 CLI。默认情况下，它读取 v1153 归档里的 seed corpus JSON，并把训练结果写到 `output/unassisted-loss-suffix-repair-training-run-v1154`。如果传了 `--run-training`，它会调用 `scripts/train.py`，把 `prepared_corpus_v1153.txt` 当作训练输入。

真实运行命令是：

```powershell
python scripts/run_unassisted_loss_suffix_repair_training_v1154.py --out-dir output\unassisted-loss-suffix-repair-training-run-v1154 --run-training --require-training-ready --force
```

这个命令跑出的训练日志很完整：`tokens=347`、`vocab_size=22`、`parameters=4,048`、`step=60`，而且 `train_loss` 和 `val_loss` 都在下降。尤其值得记录的是，`sample=...` 输出里已经能看到 `sample_fixed_hit=True`、`sample_loss_hit=True`。这说明 v1153 的修订样本确实比前一版更接近当前问题点。

## 输出文件的角色

本版的输出分成两层。第一层是 `write_readability_outputs()` 生成的 JSON、CSV、TXT、Markdown 和 HTML，它们是训练证据的可读外壳。第二层是 `unassisted_loss_suffix_repair_training_handoff_v1154.json`，这是下一版 replay 的 handoff 入口。handoff 里保留了 checkpoint、tokenizer、holdout_prompts、next_step 和 `promotion_ready=False`，确保后续 replay 能直接从这份训练结果接过去，而不会再去猜文件路径。

这份 handoff 很重要，因为它代表了版本链的真正衔接：v1153 负责修 seed，v1154 负责训练，v1155 只要沿着 handoff 再做一轮 replay，就能判断这个修订是否真的改善了 target-free holdout 的表现。

## 为什么这版仍然不是 promotion

尽管训练结果比前面更漂亮，v1154 仍然不算 promotion evidence。原因很简单：它只证明了训练过程和训练样本都对了，还没证明同一组 target-free holdout prompts 真的恢复了 `loss` 后缀。对这条路线来说，能不能在 sample 上看到 `loss` 是次要的，能不能在固定 holdout 上稳定看到 `loss` 才是关键。

所以本版的角色是“训练侧证据收口”。它把 v1153 的 seed revision 变成了真实 checkpoint，但真正的能力判断仍然要留给下一版 replay comparison。这个顺序是必要的，因为只有先确认训练素材和训练过程都没问题，后面的 replay 结果才有解释力。

## 一句话总结

v1154 把 v1153 的 loss-suffix 修订语料真正训成了一个 bounded checkpoint，train/val 都下降，sample 同时命中 fixed 和 loss，但它仍然只是训练证据，下一步必须交给 replay 比较来验证 holdout 恢复。
