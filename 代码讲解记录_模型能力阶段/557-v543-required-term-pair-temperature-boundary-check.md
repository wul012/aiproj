# v543 required-term pair temperature boundary check 代码讲解

## 本版目标和边界

v542 证明 `top_k=2` 能让 seed `535` 恢复 pair-full，但剩余 seed 仍有 first-token gap。v543 做两件事：第一，把 v541 的 decode boundary CLI 参数化，允许从命令行传入自定义 decode spec；第二，用 v542 的真实 checkpoint 跑 temperature 矩阵，检查 rank-2 token 是否能通过温度被采样出来。

本版不重训模型，不修改训练 corpus，也不把 decode 诊断结果当成最终模型稳定性结论。

## 关键修改文件

- `src/minigpt/model_capability_required_term_pair_decode_boundary_check.py`
  - 新增 `parse_decode_spec()` 和 `parse_decode_specs()`。
  - spec 格式为 `id:top_k:temperature:max_new_tokens`。
  - 没有传入自定义 spec 时仍使用原来的 `DEFAULT_DECODE_SPECS`，保持默认行为兼容。
- `scripts/run_model_capability_required_term_pair_decode_boundary_check.py`
  - 新增可重复的 `--decode-spec` 参数。
  - 将解析后的 spec 传入 builder。
- `tests/test_model_capability_required_term_pair_decode_boundary_check.py`
  - 新增解析成功和解析失败的测试。

## 核心数据结构

自定义 decode spec 是一个固定 schema：

```text
spec_id
top_k
temperature
max_new_tokens
```

CLI 输入例子：

```text
topk2-t080-n12:2:0.8:12
```

解析后进入 builder：

```text
{"spec_id": "topk2-t080-n12", "top_k": 2, "temperature": 0.8, "max_new_tokens": 12}
```

这让后续实验可以在命令行组织矩阵，而不是每次改源码。

## 真实实验

v543 读取 v542 top-k2 stability report，并运行五组 decode spec：

```text
greedy-k1-t020-n12
topk2-t040-n12
topk2-t080-n12
topk2-t120-n12
topk4-t080-n12
```

结果：

```text
baseline_pair_full_seed_count=1
best_spec_id=topk2-t080-n12
best_pair_full_seed_count=2
decision=required_term_pair_decode_boundary_improves_pair_surface
```

seed `535` 和 `2535` 在 `top_k=2, temperature=0.8` 下 pair-full；seed `1535` 仍失败。

## 链路角色

v543 的价值是把解码边界从“固定代码矩阵”变成“可配置实验入口”。这对后续模型能力推进很重要：当目标是观察 tiny GPT 的真实能力边界时，参数矩阵必须能被复现、归档和再次调整，而不是散落在临时脚本里。

## 测试覆盖

单测新增断言：

- `parse_decode_spec("topk2-t080-n12:2:0.8:12")` 能得到正确字段。
- `parse_decode_specs()` 能解析多条 CLI 输入。
- 错误格式会抛出 `ValueError`。

原有 builder 测试继续覆盖改善、无改善、输入失败和 sidecar 输出。真实验证还包括 v542 checkpoint replay、Playwright MCP 截图、全量 pytest、source encoding 和 `git diff --check`。

一句话总结：v543 把 fixed/loss pair 的解码实验入口参数化，并发现 `top_k=2, temperature=0.8` 能把可恢复 seed 提升到 `2/3`。
