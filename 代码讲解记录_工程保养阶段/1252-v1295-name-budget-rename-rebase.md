# 1252 - v1295 名字预算的重命名换底:红掉的 CI 用一个可证明中立的新工具修绿

## 本版目标与不做什么

v1294 推上去之后 CI 红了:**Name budget gate 失败,33 条"新"违规**。
本版做三件事:(1) 查明失败机理并给出正确的修复——不是回滚、不是手改
基线,而是给 name_budget 补一个**可证明中立**的重命名换底功能;
(2) 用它把 v1294 的重命名合法过闸,main 恢复绿;(3) 把"本地关门必须
跑全量 CI 闸门清单"写死进 AGENTS.md——这是今天第四次栽在
"本地检查 ⊊ CI 检查"这同一类坑上。不做什么:不回滚 v1294 的重命名;
不动名字预算的判定语义(max_name_length、扫描范围、失败条件全部原样);
不给任何"净增违规"开口子。

## 失败机理

name-budget 基线按 **(路径, 限定名) 的 sha256 digest** 记录 7,515 条
历史长名违规。v1294 把 6 个模块文件改了名——文件内部的历史长函数名/
长常量名(它们是家族公共 API,消费网横跨几十个模块,不属于文件重命名
批的范围)原样搬到了新路径下,于是同样的 33 条违规换了 digest:
报告显示 **new 33 + resolved 33,总数 7,515 不变**。闸门的更新机制
(`update_allowed = … and not new_digests`)拒绝任何有新 digest 的更新
——这个"永不放进新违规"的政策本身是对的,它只是没有"重命名"这个概念。

## 修复:rebase_renamed_paths(可证明中立才放行)

```python
新条目 := 当前扫描中不在基线里的违规
被解条目 := 基线里不在当前扫描中的 digest,其元数据取自旧树扫描
放行条件 := multiset[(kind, qualname, length)](新条目)
          == multiset[(kind, qualname, length)](被解条目)
```

即:去掉路径维度后,违规存量**逐条一一对应**才允许换底;任何净增、
任何长度变化、任何拿不到旧树元数据的 digest,一律拒绝(None)。
棘轮不可能从这扇门里松掉——这不是豁免,是给"文件重命名不产生新长名"
这个事实一个机器可验证的表达。配套脚本
`scripts/rebase_name_budget_renames.py` 用 `git worktree` 检出旧 ref
(默认 HEAD~1)做旧树扫描;实跑输出
`status=rebased violation_count=7515 (was 7515)`,name-budget 闸门
随即 pass、new=0。

两个 Windows 现实问题也在实跑中解决:归档树里有逼近 MAX_PATH 的深路径,
worktree 检出在长临时前缀下直接炸——先换短兄弟路径仍差 13 个字符,
最终用 `git -c core.longpaths=true` 按次启用长路径;工具自带
try/finally 清理 worktree。

## 第四次同类坑与规则升级

v1287 关门漏跑 ratchet、漏了 pytest-import;v1290 读错闸门字段;
本次漏跑 name-budget(且随后本地全量扫闸时又当场抓到新代码的
strict_format 失败——ruff format 对 strict 路径的格式检查也是静态闸门
的一部分,反斜杠续行不合家规,`ruff format` 一键归位)。同一类错误
第四次出现,AGENTS.md 的 CI-parity 规则升级为:**关门前把 ci.yml 里
每一个 `run:` 闸门脚本全部本地跑一遍**(全是秒级),读各自的
`status=pass` 机器字段;文件重命名类版本必须走 v1295 的换底工具。

## 测试与验证

- 新测试 5 个(pytest-import-free):中立换底放行、长度变化拒绝、
  净增拒绝、旧树元数据缺失拒绝、纯删除拒绝(纯删除属于正常更新路径,
  不该走换底门)。连同既有 name_budget 测试 14/14。
- 全量本地闸门扫描:15 个 check_* 全 pass(normalization_guard 的
  通过态是 `status=ready`,输出形制与其余闸门不同,已记入认知)。
- 全量套件另行背书(数字见提交信息);CI 绿由收口后的 run 证实。

## 工程教训

1. **闸门缺概念时,补概念,不绕闸门**:手改基线 JSON 三分钟就能让 CI
   绿,但那会把"基线是机器维护的证据"这个前提砸掉。给工具补一个带
   数学放行条件的功能,慢一个小时,换来这扇门永远可审计。
2. **"本地绿"必须定义为"CI 的全集绿"**:挑着跑闸门,漏掉的那个
   永远恰好是会红的那个——今天第四次。规则现在写死:全量扫。
3. **红 main 期间的优先级排序**:先判"回滚 vs 前修"的时长与风险,
   本例前修与回滚同为一次 push + 一轮套件,且前修产出可复用的工具,
   故选前修;若前修需要多轮探索,应先回滚止血。

产物:`rebase_renamed_paths`(name_budget.py)+
`scripts/rebase_name_budget_renames.py` + 5 测试;
`docs/elegance/name-baseline.json` 换底(7,515 → 7,515,零净变);
AGENTS.md CI-parity 规则升级为全量扫。v1294 的重命名批就此合法收口,
后续批次的关门清单里换底工具成为标准件。
