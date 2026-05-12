# 08 v3 测试和文档归档讲解

这一篇讲的是 v3 如何验证 BPE tokenizer，并把结果归档到 `a/3`。

核心流程是：

```text
扩展 tokenizer 单元测试
 -> inspect_tokenizer.py 查看 BPE merge
 -> 用 --tokenizer bpe 跑真实训练 smoke
 -> 用 generate.py 自动加载 BPE tokenizer
 -> 截图归档到 a/3/图片
 -> 在 a/3/解释/说明.md 写清命令和意义
```

新增测试覆盖：

```text
CharTokenizer save/load
BPETokenizer 学到重复 pair
BPETokenizer save/load
load_tokenizer 自动识别 char 或 bpe
```

BPE smoke：

```powershell
python -B scripts/train.py --tokenizer bpe --bpe-vocab-size 260 ...
```

训练输出里会出现：

```text
tokenizer=bpe
```

并且 `tokenizer.json` 会保存：

```text
type: bpe
merges: [...]
```

生成 smoke：

```powershell
python -B scripts/generate.py --checkpoint tmp/v3-bpe-smoke/checkpoint.pt --prompt 人工智能
```

这里没有手动指定 tokenizer 类型，因为 `generate.py` 会通过 `load_tokenizer` 自动识别 checkpoint 旁边的 `tokenizer.json`。

一句话总结：v3 的验收重点是证明 BPE 不只是能训练出来，还能保存、加载、解释，并被训练/生成脚本统一使用。
