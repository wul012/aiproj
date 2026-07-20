# 1258 - v1301 去重正式批 1:23 簇 1,607 份拷贝归一,dup_def_stock 227 → 204

## 本版目标与不做什么

优雅收官报告把"重复函数体存量 227"标为 7.5 → 9 价目表的第三项;
本版开烧。批 1 取**语义最清楚、体量最大**的两族:check/exit-code 族
(`_check` × 375、`resolve_exit_code` 各变体 × 277)与 HTML/路径小助手族
(`_card` × 463、`_check_row` × 252、`_term` × 83、`_path_exists` × 157)——
23 个簇、968 个成员模块、1,607 份内联拷贝,全部改为从宿主模块的
别名 import。不做什么:不动 42 个被模块级常量(READY_KEY 等)绑住的
簇(需参数化,另立批次);不动 `_style` 27 变体家族(变体语义需逐个
命名,手工地图活);不新建平铺模块(flat 棘轮 1355 封顶——宿主只能
是既有公共模块)。

## 三条硬约束决定了宿主与形态

(1) **架构契约**:owner 包子模块必须是纯门面(任何 def 都是违规),
公共实现进不去;(2) **flat 棘轮**:平铺目录只能减不能增,新模块不许建;
(3) **file-size 棘轮**:500 行警戒线下自由生长。三者合取 ⇒ 宿主只能是
既有平铺公共模块的富余空间:`report_check_common`(32 行,v1187 的
check 三件套老家)接 check/exit-code 族 13 个宿主函数;`report_utils`
(179 行,html_escape/csv 工具老家)接 HTML/路径族 5 个。

关键设计判断:`resolve_exit_code` 的十几个"变体"其实是**关键字参数名
不同**(require_training_ready / require_diagnostic_ready / ...)——CLI
按关键字传参,统一签名会破坏成员公共 API。所以不统一:每个变体在宿主
里有自己的名字(`resolve_exit_code_<kw>_ready`),成员按旧本地名
`as resolve_exit_code` 引回,契约逐字节保持。纯代码风格双胞胎
(三元式 vs if 式、拼接 f-string vs 展开式)经等价性人工判定后共享
一个宿主函数——计划 JSON 里每簇标注 verbatim / equivalent 及理由。

## 执行器的新难点:删 def 会孤儿化 import

重命名批次不改成员内容结构;去重批次**删代码**,带出两个新问题:
(1) 被删 def 是 `html_escape`/`Path` 在该模块的唯一使用者时,残留
import 变成新 F401 → 静态门崩。执行器按 AST 精确判定:被删函数的
自由名在删后无引用者 ⇒ 从 import 语句中摘除该名(多名 import 重写,
`__future__` 永不动)。(2) 成员的 `resolve_exit_code` 若只被外部脚本
消费(模块内无调用点),插入的 import 是纯再导出 ⇒ 按 v1292 惯例挂
`# noqa: F401 (re-export)`。两遍式结构(PASS 1 全量只读断言,PASS 2
才落盘)延续——968 个文件一次通过,静态门 0 新问题。

## 全扫抓住第八类耦合:类型闸门的 Any 传染

15 项快门里 type_analysis 独崩:四个严格类型脚本报 no-any-return。
根因:成员模块(mypy 严格目标)的 `resolve_exit_code` 现在经由
`report_check_common` 引入,而后者**不在** mypy 目标集 → mypy 视其为
Any → 脚本的 `return resolve_exit_code(...)` 返回 Any。修法是收紧而
不是绕开:把 `report_check_common` 加进 mypy 目标集(22 → 23,
shared_report_contract 组),宿主升为严格类型,Any 链闭合,0 诊断。
教训:**把实现抽进公共模块,等于把它抽进了最严格消费者的类型边界**——
宿主的类型纪律必须匹配其最严格的成员,抽取清单要过一遍"成员是否
在严格类型目标集"的推演。

## 数字

| 指标 | 批前 | 批后 |
|---|---|---|
| dup_def_stock | 227 | **204**(-23,计划数精确命中) |
| 内联拷贝 | — | -1,607 份(约 4,000 行纯复制粘贴消失) |
| 宿主函数 | — | +18(report_check_common 13 + report_utils 5) |
| 身份测试 | — | >1,500 个 import 绑定逐一断言 `is` 宿主对象(双运行器) |
| mypy 目标 | 22 | **23**(宿主入严格集) |

22 项 CI 闸门本地全扫全绿;优雅基线拧紧至 dup=204。

## 工程教训

1. **删代码比移代码危险**:重命名五批零内容变更,去重第一批就带出
   import 孤儿化与 Any 传染两类新耦合——"删"的影响半径是使用图,
   不是文件名图。AST 级自由名分析是唯一可靠的孤儿判定器。
2. **变体不可强行归一**:关键字参数名是公共 API 的一部分;去重的
   单位是"字节等价或经证明的语义等价体",不是"长得像的东西"。
3. **等价性判定要落档**:计划 JSON 里每簇的 verbatim/equivalent 标注
   就是审计线索——谁批准了哪两个身体等价、依据是什么,走查可复核。

产物:report_check_common +13 宿主函数(入 mypy 严格集)、report_utils
+5、968 成员模块瘦身、tests/test_report_dedup_common_v1301.py(全量
身份回归)、优雅基线 dup 227 → 204。剩余:181 簇(42 常量绑定 +
_style 变体家族 + 长尾),分批续烧。
