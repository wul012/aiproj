# 1250 - v1293 基线归零 + 优雅 ratchet:债清完的那一刻把闸门焊死

## 本版目标与不做什么

优雅计划第四级,一版两件事,合成正常工作量:(1) 修掉静态基线里最后一条
——data_prep 的潜在 NameError(F821,真 bug 不是风格),让静态分析基线
从 271 出发正式**归零**;(2) 在债清零的同一版里上线**全库优雅 ratchet**:
四个结构性指标冻结在当前值,只许降不许升,把 v1295+ 批量重命名/子包化
的成果做成单向棘轮。不做什么:不动任何实验语义;不在本版开始搬文件
(那是 v1295+ 的批次工作,本版先把"不许变坏"焊死)。

## 第一件事:data_prep 的潜在 NameError

`build_dataset_version_manifest(dataset, report=None, quality=None, …)` 在
`quality=None`(默认值!)时走回退分支调用 `build_dataset_quality_report`
——而这个名字只在**另一个函数**(write_dataset_bundle,行 238)的函数内
import 里存在。任何省略 quality 的调用者会当场 NameError。它活到今天只
因为现有三个调用点(data_prep 自身、scripts/train.py、测试)恰好都显式
传了 quality。为什么不能模块级 import?**循环依赖**:data_quality 从
data_prep 导入 PreparedDataset——这正是行 238 用函数内 import 的原因,
修复照抄同一模式(函数内 import + 注明循环原因的约束注释),并加回归
测试:不传 quality 调用,断言 manifest["quality"]["status"] 非空。
ruff F821 全仓库归零,`--update-baseline` 后 **baseline = current = 0**。

从 v1290 启动时的 271 到 0,静态债的收束路径:271 →(v1291 机械四类
-118)→ 153 →(v1292 审计清扫 -152)→ 1 →(本版 -1)→ **0**。

## 第二件事:优雅 ratchet(elegance_ratchet)

四个指标,全部对着 6/10 评分时点名的结构病灶:

| 指标 | 冻结值 | 对应病灶 |
|---|---|---|
| flat_dir_file_count | 1355 | src/minigpt 扁平命名空间(无子包) |
| long_name_stock | 282 | >120 字符的模块名家族(最长 202) |
| max_stem_length | 202 | receipt_index×8 的病理命名上限 |
| dup_def_stock | 227 | 跨 ≥3 模块逐字节重复的函数体 |

dup_def_stock 用无位置信息的 `ast.dump` 做函数体指纹——v1290 抓的
`_median` × 12 就是这一类;冻结值 227 说明 model_capability 家族里
克隆函数体的存量远比弧上那 12 份大,现在它是被度量、被锁死的数字。

机制完全复用 v1187 抽出的 report_check_common 检查件
(check_row/collect_failures/resolve_exit_code)和 check_file_size_ratchet
的脚本形制;`--update-baseline` 只在 status=pass 时落盘(结构上只紧不松);
CI 在 File size ratchet 之后新增 Elegance ratchet 步骤
(check_ci_workflow_hygiene 本地先行验证通过——v1290 的 CI-parity 教训
落实到位)。刻意不重复已有闸门:文件行数归 file_size_ratchet 管,
新名字长度预算归 name_budget 管;本版四指标管的是**存量结构债**。

一个诚实的细节:elegance_ratchet.py 自己让扁平目录 +1(1354→1355 时代
的账),基线冻结在含它的状态——棘轮从"本版收口后"起算,它是最后一次
被允许的增长。

## 测试与验证

- 新测试 4 个(pytest 风格、pytest-import-free):合成迷你项目树上验证
  四指标计数(长名、≥3 模块重复体阈值)、基线处 pass/增长即 fail 且
  失败行精确定位、**update 只紧不松**(fail 时拒绝落盘、基线原样)、
  输出文件形制。初版有一个测试笔误(check_row 的键是 `id` 不是
  `check_id`)——修的是测试的访问键,不是被测行为。
- 门:12/12 聚焦测试;静态 status=pass / current=0;elegance ratchet
  status=pass(四指标 = 基线);CI workflow hygiene 本地 pass;
  全量套件另行背书(数字见提交信息)。

## 工程教训

1. **债清零的同一版必须上锁**:清零状态是最脆的时刻——没有闸门,
   下一个赶工版本就能把它悄悄弄脏。ratchet 和归零同版落地,窗口为零。
2. **潜在 bug 的年龄不是安全证据**:F821 在基线里躺了很久,"从没炸过"
   只说明调用面恰好没踩到默认参数路径;修复 + 回归测试才是证据。
3. **新闸门要和旧闸门划清管辖**:先盘点已有 ratchet(file size、
   name budget)再定指标,四个新指标全部是没人管的存量结构债,
   零重叠零冲突。

产物:data_prep 修复 + 回归测试;`src/minigpt/elegance_ratchet.py`、
`scripts/check_elegance_ratchet.py`、`docs/static-analysis/
elegance-baseline.json`、`tests/test_elegance_ratchet_v1293.py`、
ci.yml 新步骤。静态基线 **0**;结构基线 {1355, 282, 202, 227} 只降不升。
下一版 v1294+ 开始批量重命名+子包化,每批收口后用
`--update-baseline` 把棘轮拧紧一格。
