# v1130 publication naming readability 代码讲解

## 本版目标和边界

v1130 是工程后期保养五版的第一版，目标是先做“命名止血”。这里的止血不是把历史文件全部改短，也不是重写 publication receipt 链路，而是先把命名问题变成一个可运行、可归档、可复查的报告：哪些历史文件因为重复 `receipt_index` 而形成阅读压力，哪些文件名已经超过终端一屏可读范围，后续新增 publication 类脚本应该采用哪些短别名。这样做的好处是风险低、边界清楚，并且能为后续几版保养建立事实基础。

本版明确不做三件事。第一，不移动 v1098 到 v1129 形成的历史治理文件，因为这些文件已经被 README、f 目录证据、测试和 tag 历史引用，贸然移动会制造兼容风险。第二，不批量重命名长模块，因为当前长名虽然阅读成本高，但在 Python import、测试引用和归档文件名之间已经形成稳定契约。第三，不把命名扫描结果当成 CI 阻断项。本版真实扫描输出 `status=watch`，这代表“历史压力需要监控”，不是“当前版本失败”。真正需要阻断的是未来新文件继续扩大同类命名，而不是历史文件本身。

外部建议里把 aiproj 的第一优先级定为“命名止血”，原因很准确：项目已经从 MiniGPT 训练脚本扩展为 AI 治理工程，publication receipt、receipt index、review、contract check、no-promotion boundary 等链路越来越厚。如果继续把完整语义全堆进文件名，就会出现 `randomized_holdout_publication_receipt_index_receipt_index_receipt_index...` 这种读者很难定位职责的名字。v1130 不是否定这些链路的价值，而是把下一阶段的新命名规则先立住。

## 新增文件和职责

`src/minigpt/readability_report_artifacts.py` 是本版新增的通用可读性报告 artifact helper。它负责把后续保养类 report 写成 JSON、CSV、text、Markdown 和 HTML 五种格式。之所以先抽这个 helper，是为了避免后续五版每一版都重复写一套 Markdown/HTML/CSV 渲染器。它提供 `render_readability_text`、`render_readability_markdown`、`render_readability_html`、`write_readability_csv` 和 `write_readability_outputs`，让具体业务模块只关心 report 结构，不关心输出格式细节。

`src/minigpt/publication_naming_readability.py` 是本版的业务中心。它定义扫描范围 `scripts`、`src/minigpt` 和 `tests`，检查 Python 文件名中的 `receipt_index` 重复次数和文件名长度。报告不会扫描整个仓库的 Markdown、JSON 或历史截图，因为本版要解决的是新代码入口和模块名压力，而不是证据归档文件名。模块里保留了 `SHORT_ALIAS_POLICY`，明确把“publication receipt index”推荐为 `pub_receipt_index`，把“publication receipt review”推荐为 `pub_receipt_review`，把“receipt contract check”推荐为 `receipt_contract_check`，把“randomized holdout publication”推荐为 `holdout_pub`。

`scripts/publication/check_publication_naming_readability_v1130.py` 是新的分层 CLI。它没有放在平铺的 `scripts/` 根目录，而是放在 `scripts/publication/` 下，正好落实外部建议里的 scripts 分层方向。这个入口支持 `--root`、`--out-dir`、`--require-policy-ready`、`--require-clean-new-names` 和 `--force`。其中 `--require-policy-ready` 用来确认规则本身能生成，`--require-clean-new-names` 则可以在未来更严格的场景下启用，要求扫描结果必须完全 pass。

`tests/test_publication_naming_readability.py` 覆盖了三类关键行为：历史重复 `receipt_index` 文件会被标成 `watch`；短别名文件不会生成 watch 行；真实输出和 CLI 能写出五种格式，并且 `--require-policy-ready` 返回 0。这些测试保护了本版最重要的边界：报告可以看到历史问题，但不会把历史问题误判为当前失败；短别名策略可以通过测试证明是可执行的，不只是文档建议。

## 报告数据结构

v1130 report 的顶层字段包括 `schema_version`、`title`、`generated_at`、`status`、`decision`、`summary`、`policy`、`rows`、`recommendations` 和 `csv_fieldnames`。其中 `status` 在真实仓库里是 `watch`，因为历史文件中确实存在大量重复 `receipt_index` 命名；`decision` 是 `publication_short_alias_policy_ready`，说明命名止血策略已经可以被后续版本消费。

`summary` 是给 CLI、README 和人工快速阅读的摘要。真实运行里它包含 `scanned_file_count=837`、`repeated_receipt_index_file_count=548`、`long_name_file_count=808`、`policy_ready=True` 等字段。这些数字说明问题不是个别文件，而是高速治理链推进后的系统性阅读成本。这里的价值在于量化：以后如果新短名策略生效，新增文件就不应该再提高这些压力指标。

`policy` 是规则本体。它写清扫描范围、legacy 文件只作为 watch item、新 publication 文件必须使用短别名、重复 token 是 `receipt_index`、重复限制是 1、文件名长度建议限制是 96，以及短别名映射。这个字段让报告不只是结果，还能解释“为什么这样判断”。后续如果需要把命名规则接入更严格的 preflight，可以直接读取 policy，而不用从 Markdown 里解析自然语言。

`rows` 是压力明细。每一行包含 `path`、`kind`、`name_length`、`repeat_count`、`status` 和 `recommendation`。真实报告只保留前 80 行，避免 HTML 和 Markdown 过大。这个选择是刻意的：v1130 的目的不是列出全部 548 个 legacy watch 文件，而是让读者看到最严重的命名压力样本，并理解后续要采用短别名。完整扫描数量已经在 summary 中保留。

## 运行证据

本版真实运行命令是：

```powershell
python -B scripts\publication\check_publication_naming_readability_v1130.py --out-dir f\1130\解释\naming-readability-v1130 --require-policy-ready --force
```

输出结果显示 `status=watch`、`decision=publication_short_alias_policy_ready`、`scanned_file_count=837`、`repeated_receipt_index_file_count=548`、`long_name_file_count=808`、`policy_ready=True`。这些字段一起说明：历史命名压力确实存在，但策略层已经 ready。这里选择 `watch` 很重要，如果直接把历史问题标成 fail，就会让维护任务变成大规模重命名；如果标成 pass，又会掩盖命名压力。`watch` 正好表达“可以继续推进，但必须改变新增文件习惯”。

Playwright MCP 打开了 `f/1130/解释/naming-readability-v1130/publication_naming_readability_v1130.html`。页面快照能看到标题、摘要卡片、`Naming Pressure Rows` 表格和 `Recommendations` 区域。截图保存为 `f/1130/图片/v1130-naming-readability.png`。第一次 full-page 截图因为页面较长触发浏览器截图错误，随后改成固定视口截图，保留了标题、summary 和表格入口，足够证明 HTML 报告可打开、可读、可审阅。

## 测试覆盖

focused test 是 `tests/test_publication_naming_readability.py`，结果为 `3 passed in 0.21s`。第一条测试构造一个包含重复 `receipt_index` 的临时脚本，确认 report 进入 `watch`，同时 `require_policy_ready` 返回 0、`require_clean_new_names` 返回 1。这个测试保护的是“历史压力可见，但严格清洁模式可选”。第二条测试构造 `scripts/publication/build_pub_receipt_review_v1130.py` 这样的短名文件，确认 report 为 `pass`，并且文件名长度低于限制。第三条测试覆盖 artifact 输出和 CLI，确认 JSON、CSV、text、Markdown、HTML 都能生成。

本版还执行了 py_compile，覆盖新增 helper、业务模块、CLI 和测试。后续版本在最终收口时还会跑 source encoding、diff check 和更大范围 pytest。v1130 的 focused test 不试图证明所有 publication receipt 历史链路都正确，它只证明命名止血报告本身能扫描、能输出、能区分 legacy watch 与短名 pass。

## 维护意义

v1130 的维护意义在于改变后续增量的方向。历史长名暂时保留，因为它们是已有证据链的一部分；新增文件从本版开始有了短别名策略和 `scripts/publication/` 子目录。这样后续做 README 拆分、scripts 分层、receipt 模板和 artifact 对照表时，就不会继续把所有上下文塞进文件名。工程后期保养最怕用一次大重构制造新风险，v1130 选择的是先建立规则和观测点，再逐步迁移入口。

## 一句话总结

v1130 把 aiproj 的 publication 长命名问题从主观抱怨变成可运行的 `watch` 报告和短别名止血策略，让后续工程保养可以在不破坏历史证据链的前提下开始降低阅读成本。
