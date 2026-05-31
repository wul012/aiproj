# v588 required-term pair ten-version closeout

## 本版目标和边界

v588 收口 v579-v588 十版连续推进。它不训练、不新增 corpus mode、不增加新治理链，而是汇总这一轮模型能力路线的事实结果，并跑全量测试确认工程状态。

## 本轮路线

```text
v579 branch-binding baseline
v580 whitespace diagnostic
v581 branch-binding no-space
v582 branch-binding comparison
v583 branch-binding route decision
v584 target-anchor seed check
v585 target-anchor comparison
v586 target-anchor route decision
v587 objective closeout
v588 ten-version closeout
```

## 核心结论

没有任何新路线在 seed `3535` 上达到 pair-full。

branch-binding v1/v2 结果更差：

```text
no visible hit
```

target-anchor 恢复了 partial fixed：

```text
fixed hit only
loss missing
```

因此 v586 将 target-anchor 判为 residual-only，v587 要求下一步转向 loss-branch objective。

## 验证

本版全量验证：

```text
python -m pytest -q -o cache_dir=runs\pytest-cache-v588-full
1165 passed in 189.28s

python -B scripts\check_source_encoding.py --out-dir runs\source-encoding-hygiene-local-v588
status=pass
source_count=667
syntax_error_count=0

git diff --check
pass
```

## 证据归档

运行证据：

```text
e/588/解释/model-capability-required-term-pair-ten-version-closeout/
e/588/图片/v588-ten-version-closeout.png
```

## 一句话总结

v588 证明这轮十版没有带来 pair-full 能力提升，但有效排除了 branch-binding v1/v2，保留 target-anchor residual evidence，并把下一步明确指向 loss branch objective。
