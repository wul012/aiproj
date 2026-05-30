# v526 generator blocked-token profile 代码讲解

## 本版目标与边界

v526 的目标是把 v524/v525 的 newline-suppressed decoding 结果沉淀为 core generator 的可选能力。此前 v524 probe 在模块内部手写了一段逐 token sampling 逻辑；这容易和 `MiniGPTGenerator` 的正式生成路径分叉。v526 通过 `GenerationRequest.blocked_token_texts` 把能力放回正式生成链路。

本版默认不屏蔽任何 token，不改变已有脚本、服务和普通生成请求的行为。只有显式传入 blocked token texts 时，采样 logits 才会屏蔽对应 tokenizer entries。

## 前置链路

前置版本：

- v524：单 checkpoint 证明 newline-token suppression 可把 strict hit 从 `0/4` 恢复到 `4/4`。
- v525：跨 v518/v523 两个 focus checkpoints 证明该信号稳定。

v526 将该实验能力升级为受控的 generator feature。

## 关键文件

- `src/minigpt/server_contracts.py`
  - `GenerationRequest` 新增 `blocked_token_texts: tuple[str, ...] = ()`。
  - `parse_generation_request()` 支持从 payload 读取 `blocked_token_texts`。
  - `InferenceSafetyProfile` 新增 `max_blocked_token_texts`，限制请求规模。
  - `GenerationResponse` 与 `GenerationStreamChunk` 记录 blocked token 元数据。
- `src/minigpt/model.py`
  - `sample_next()` 新增 `blocked_token_ids`。
  - logits softmax 前把 blocked ids 设为 `-inf`。
  - 若 blocked ids 覆盖整个 vocab，抛出结构错误。
  - `generate()` 把 blocked ids 传给 `sample_next()`。
- `src/minigpt/server_generator.py`
  - 根据 tokenizer `itos` 查找包含 blocked substring 的 token id。
  - 普通 generate 和 stream 都走同一套 blocked token id。
- `src/minigpt/model_capability_required_term_pair_loss_alias_newline_suppression_probe.py`
  - 删除 probe 私有采样实现。
  - 改为调用 `MiniGPTGenerator(...).generate(GenerationRequest(..., blocked_token_texts=...))`。
- `tests/test_model.py`
  - 覆盖 blocked token id 会被排除，以及不能 block 全 vocab。
- `tests/test_server.py`
  - 覆盖 request parsing、去重和 safety limit。

## 核心数据结构

`GenerationRequest` 新字段：

```text
blocked_token_texts: tuple[str, ...] = ()
```

语义：

- 空 tuple：不启用 token 屏蔽。
- 非空：遍历 tokenizer `itos`，凡 token text 包含任一 blocked substring，即加入 blocked ids。
- 例如 `("\n", "\r")` 会屏蔽换行相关 token。

`GenerationResponse` 新字段：

```text
blocked_token_texts
blocked_token_count
```

它们用于审计请求是否启用了 blocked-token profile，以及实际命中了多少 tokenizer entries。

## 核心流程

1. API 或调用方传入 payload。
2. `parse_generation_request()` 解析 `blocked_token_texts` 并去重。
3. `MiniGPTGenerator.generate()` 加载 tokenizer 和模型。
4. `_blocked_token_ids()` 根据 tokenizer vocabulary 解析 token ids。
5. `MiniGPT.generate()` 将 blocked ids 传入 `sample_next()`。
6. `sample_next()` 在 top-k 之前屏蔽 logits。
7. response 记录 blocked token metadata。

这个顺序很重要：先屏蔽 token，再做 top-k，才能让 top-k=1 时从原本的 newline 候选退到下一个合法 token。

## 真实结果解释

v526 真实运行结果：

```text
baseline_strict_hit_count=0
suppressed_strict_hit_count=4
suppressed_strict_gain_count=4
```

这说明把 suppression 接入 core generator 后，v524 的实验证据仍然成立。JSON 中 suppressed rows 的 `excluded_token_count=1` 证明 tokenizer 中确实有一个 newline 相关 token 被屏蔽。

## 测试覆盖

测试覆盖：

- `MiniGPT.sample_next()` 在 blocked ids 只剩一个合法 token 时返回该 token。
- block 全 vocab 会抛出错误，避免 softmax 全 `-inf`。
- `parse_generation_request()` 能解析、去重 `blocked_token_texts`。
- safety profile 会限制 blocked token text 数量。
- v524/v525 probe/repeat 测试继续通过，证明实验链已切到 core generator 后仍兼容。

## 运行证据

运行证据归档在：

```text
e/526/解释/model-capability-required-term-pair-loss-alias-generator-blocked-token-profile/
e/526/图片/
```

截图：

```text
e/526/图片/01-model-capability-required-term-pair-loss-alias-generator-blocked-token-profile.png
```

## 一句话总结

v526 把 newline-suppressed decoding 从一次实验实现变成默认关闭、可审计、可复用的 core generation capability。
