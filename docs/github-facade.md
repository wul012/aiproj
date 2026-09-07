# GitHub 门面整理 2026-09-08

## Design

共享 SVG engine 用标题、角色、颜色、三段标签数据生成封面；SVG 无脚本、外部字体或远程依赖。
首屏先呈现项目功能与快速开始，原 HEAD README 全文保留在 details 历史区，不移动既有证据。

## Scope

仅 README、封面和本记录，以及 GitHub About/Topics；不改源码、tests、依赖、fixture、历史标签或版本模式。
仓库仍为 `wul012/aiproj`。这是一项明确授权的展示文档整理，不新建业务版本标签。
现有用户文件保留，仅显式暂存本次三个文档资产。

## 需求与证据

|要求|实现|验收|
|---|---|---|
|识别项目|ML RESEARCH / MiniGPT Lab / 专属配色|GFM 首屏检查|
|可定位功能|三项核心能力、代码入口与运行命令|新增链接存在性与原命令核对|
|不夸大成果|版本化证据、明确运行边界|既有文档契约保持|
|不丢历史|原 README 原文折叠保留|与修改前 HEAD 原文逐字比对|
|上线可用|commit/push 与 GitHub description/topics|远端 SHA、README 和渲染检查|

验证结果记录在本次任务输出；不宣称重新跑过全部业务测试或模型训练。
失败条件：文档合同失败、旧文内容丢失、封面裁切、新链接断开或意外暂存用户文件。

## 本地验收结果

AI 文档/配置/根目录 hygiene 共 19 项通过；Project docs readability 15/15、status=pass。
新增代码入口链接均能定位；原 HEAD README 逐字保留；SVG XML 校验通过。
GitHub GFM 渲染后的 1200px 与 390px 视口检查：横向溢出为 false，封面加载成功，历史区默认折叠。
完整业务测试和训练未在这次文档任务中重跑。

关系校准：Java / Node / mini-kv 为三项目协作；AI 为独立研究项目。统一封面仅代表同一作者的作品，不代表四者共同构成系统。历史原文中的制品校验关系不作为新的架构主张。

AI 额外检查：CI fast-gate sweep 共 18 个已有 check 入口均通过。最初缺少 ruff/mypy，使用临时工具目录补齐后 static/type gate 均 status=pass，未修改 requirements 或源码。
