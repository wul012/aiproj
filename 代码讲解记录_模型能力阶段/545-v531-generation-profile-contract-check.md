# v531 generation profile contract check 代码讲解

## 本版目标和边界

v531 接在 v529 和 v530 后面。v529 把 newline suppression 暴露成 `suppress_newline_tokens` generation profile，v530 又让服务端通过 `/api/generation-profiles` 发布 profile registry，并让 playground 运行时加载它。

本版解决的问题是：这些证据现在散在 endpoint JSON、health JSON、API response、CLI 输出和 playground HTML 里，后续如果任一端漂移，很难第一时间发现。v531 因此新增 `generation_profile_contract_check`，把这些归档证据放在一份合同检查里。

本版明确不做三件事：

- 不重新训练模型。
- 不改变默认 `default` generation profile。
- 不把 suppression profile 说成模型能力本身，只证明它作为解码入口在多端一致。

## 关键文件

- `src/minigpt/generation_profile_contract_check.py`
  - 负责读取证据源、构造 check rows、汇总 `status`、`decision`、`failed_count` 和 `issues`。
- `src/minigpt/generation_profile_contract_check_artifacts.py`
  - 负责输出 JSON、CSV、text、Markdown、HTML 五种 sidecar。
- `scripts/check_generation_profile_contract.py`
  - 提供 CLI，支持 `--require-pass`，失败时返回非零状态码。
- `tests/test_generation_profile_contract_check.py`
  - 覆盖通过路径、profile 缺失、health endpoint 漂移、API profile 漂移、CLI 失败码和输出文件。
- `e/531/解释/generation-profile-contract-check/`
  - 保存真实运行产生的 check 报告。
- `e/531/图片/01-generation-profile-contract-check.png`
  - Playwright MCP 截取的 HTML 报告图。

## 核心数据结构

`build_generation_profile_contract_check()` 返回一个普通 JSON object：

```text
schema_version
title
generated_at
status
decision
failed_count
issues
checks
sources
summary
```

其中 `checks` 是本版最重要的结构。每行包含：

```text
id
category
target
expected
actual
status
detail
```

这让 HTML/CSV/text 都能消费同一个事实表，而不是每个格式重新判断一遍。

## 检查流程

1. `resolve_generation_profiles_source()` 允许输入 endpoint JSON 或其目录。如果传入目录，自动寻找 `generation-profiles.json`。
2. `_read_json_source()` 和 `_read_text_source()` 读取六类源：
   - profile endpoint JSON
   - health JSON
   - suppression-profile API response
   - playground HTML
   - default CLI 输出
   - suppression-profile CLI 输出
3. 核心检查覆盖：
   - endpoint status 为 `ok`
   - endpoint 发布 `default` 与 `suppress_newline_tokens`
   - suppression profile 的 `blocked_token_texts` 包含 `\n` 和 `\r`
   - health 的 `generation_profiles_endpoint` 是 `/api/generation-profiles`
   - health profile ids 与 endpoint profile ids 一致
   - API response 回显 `generation_profile=suppress_newline_tokens`
   - API response 的 `blocked_token_count > 0`
   - playground HTML 包含 profile select、endpoint fetch、loader 和 CLI flag
   - default CLI 输出保留 newline split，而 profile CLI 输出不含 newline 且包含 `loss`
4. 所有失败行转换为 `issues`，`failed_count=0` 时报告 `status=pass`。

## 运行证据

真实运行命令使用 v530 endpoint 与 health、v529 API/CLI 对照输出，并重新生成当前 playground HTML：

```powershell
python -B scripts\check_generation_profile_contract.py e\530\解释\generation-profiles-endpoint --health e\530\解释\generation-profiles-endpoint\health-with-generation-profiles.json --api-response e\529\解释\generation-profile-playground\api-generate-suppress-newline.json --playground-html e\531\解释\generation-profile-current-playground\playground.html --default-output e\529\解释\generation-profile-playground\default-omega.txt --profile-output e\529\解释\generation-profile-playground\suppress-newline-omega.txt --out-dir e\531\解释\generation-profile-contract-check --force --require-pass
```

结果为：

```text
status=pass
decision=generation_profile_contract_ready
failed_count=0
api_generation_profile=suppress_newline_tokens
api_blocked_token_count=1
```

值得注意的是，第一次直接使用旧 v529 `playground.html` 时检查失败，原因是旧 HTML 不包含 v530 新增的 `/api/generation-profiles` loader。这个失败不是误报，而是本版 check 的价值体现：过期 artifact 会被识别出来。

## 测试覆盖

`tests/test_generation_profile_contract_check.py` 做了五类保护：

- 合法 fixture 通过，并且 `--require-pass` 语义返回 0。
- 删除 `suppress_newline_tokens` 后失败，保护 endpoint profile registry。
- 改错 health endpoint 后失败，保护 health 与 runtime endpoint 的契约。
- 把 API response 的 `generation_profile` 改成 `default` 后失败，保护 API echo。
- CLI 在失败报告加 `--require-pass` 时返回 1，保护 CI 用法。
- 输出 writer 生成 JSON、CSV、text、Markdown、HTML，保护后续归档和截图。

## 链路角色

v531 是一个 contract-preserving 版本。它没有扩大模型能力主张，而是给 v529/v530 已有能力加上复核入口。后续如果继续扩展 profile，比如增加 top-k profile、temperature profile 或更多 blocked token profile，可以把新 profile 加入同一套 endpoint/API/playground 检查，而不必手工比对多个文件。

一句话总结：v531 把 generation profile 的多端一致性从“靠文档说明”推进为“可运行、可失败、可截图的合同检查”。
