# v238 dependabot automation 代码讲解

## 本版目标

v238 的目标是采用“4 项目加 Dependabot”的建议里最适合 aiproj 的部分：给 GitHub Actions 和 Python 依赖增加自动更新入口。

这版不是继续扩展 training portfolio comparison，而是补一个低风险、高收益的仓库维护能力，让依赖更新不再完全依靠人工发现。

## 不做什么

本版不自动合并依赖更新。

本版不改变 CI 流程、Python 版本、依赖版本约束或测试命令。

本版不引入额外 YAML 解析依赖，只用轻量文本测试保护配置形状。

## `.github/dependabot.yml`

新增 Dependabot 配置：

```text
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### GitHub Actions

`github-actions` 让 Dependabot 检查 `.github/workflows/ci.yml` 里的 action 版本。

当前 aiproj CI 使用：

```text
actions/checkout
actions/setup-python
```

这类依赖适合自动开 PR 更新，因为更新面清楚，CI 会直接验证。

### pip

`pip` 监控仓库根目录的 Python 依赖文件。

当前项目有：

```text
requirements.txt
pyproject.toml
```

Dependabot 会在检测到可升级依赖时创建 PR。它不会直接改主分支，也不会替代人工 review。

## `tests/test_dependabot_config.py`

新增轻量测试：

```text
test_dependabot_tracks_actions_and_python_dependencies
```

测试内容：

- `.github/dependabot.yml` 存在且可读。
- 配置包含 `version: 2`。
- 配置包含 `github-actions`。
- 配置包含 `pip`。
- 两个 ecosystem 都指向根目录 `/`。
- 两个 ecosystem 都是 weekly schedule。

这不是完整 YAML schema 校验，而是项目级 guard：防止后续误删配置、改错 ecosystem 或只保留其中一个更新源。

## 输入输出

输入是仓库依赖配置：

- `.github/workflows/ci.yml`
- `requirements.txt`
- `pyproject.toml`

输出是 Dependabot 在 GitHub 上按周期开出的更新 PR。

本地不会产生运行时 artifact；本版只新增配置、测试、说明和 `c/238` 运行证据。

## 运行证据

本版运行证据归档在 `c/238`：

- `图片/01-dependabot-config-test.png`
- `图片/02-dependabot-config-smoke.png`
- `图片/03-source-encoding-smoke.png`
- `图片/04-full-unittest.png`

## 证据链角色

v238 补的是工程维护自动化，不是模型能力。

它让 aiproj 开始具备基础依赖更新提醒能力，后续再接 coverage report 或 coverage gate 时，CI 的依赖面也更容易被持续维护。

## 一句话总结

v238 给 aiproj 加上 Dependabot，让 GitHub Actions 和 Python 依赖更新从人工发现变成自动 PR 入口。
