# 1251 - v1294 重命名试点批:v1012-v1015 回执簇短名化(子包化被架构合同正确地挡回)

## 本版目标与不做什么

优雅计划第五级的**试点批**:把病理命名家族里最老的一簇——v1012-v1014
receipt-packet-index 三件套(check/index/review,各带 artifacts 渲染器,
共 6 个模块,名字 185-202 字符)——**原地重命名**为短规范名
(packet_index_check_v1012 等;首版的子包化方案被架构合同挡回,见下),
旧长名路径全部留**转发 shim**;同批重命名它们的 3 个脚本和
3 个测试。试点的目的不是清完(93 个 >180 字符的模块还在),而是把
批量迁移的全部隐性耦合在最小批上暴露出来、把模式打磨到可复制。
不做什么:不动 v1015 及更上游的家族成员(它们经 shim 消费旧路径,
正好充当 shim 的活体验证);不改任何被迁模块的行为;**产物文件名常量
一个不改**(那是治理链的输出契约)。

## shim 设计:sys.modules 自替换

```python
import sys
from minigpt import packet_index_v1013 as _target
sys.modules[__name__] = _target
```

旧路径 import 得到的**就是**目标模块对象本身——`old is new` 为 True
(收口时用 importlib 双路导入断言过)。对身份敏感的消费者(公共 API
的 `is` 契约测试、attribute 访问)零差异。这比 `from X import *` 强:
不丢下划线名、不骗 lint、不复制对象。

## 最大的发现:owner 包是质量门,不是命名空间(方案被正确地挡回)

首版方案把 6 个模块迁进新子包 `minigpt/receipts/`。全量套件当场揭示:
`test_architecture_boundaries.py` 维护着一套 **owner 包合同**——src/minigpt
下任何带 __init__ 的包目录必须注册为 owner 包(core/training/evaluation/
serving/reports/governance),而 owner 包身份带着**质量门**:__init__ 必须
是带 `__all__` 的纯 facade、包内模块有 220 行上限、子模块必须是
facade-only 形制(93 处违规)。逐字节搬进去的历史治理模块根本不满足
这些标准——满足它们需要真正的规范化重构,远超"行为保持的重命名批"。

三条路:(a) 深度重构 6 个历史模块凑标准——违反本批行为保持红线;
(b) 给 receipts 开"二等包"豁免——**放松架构合同**,违反 ratchet 哲学
和两线边界;(c) **退一步:原地重命名**——短名留在扁平目录,长名 shim
照样转发,子包化让给规范化工程线自己的节奏(owner 包本来就是"新代码
优先入住、历史模块渐进规范化后迁入"的设计)。选 (c),并把
elegance 计划的命名空间目标诚实降级:本计划交付命名手术 + shim +
棘轮;flat_dir_file_count 的下降属于规范化线的长弧,不属于本计划。
这正是 v1171 拒绝千文件搬迁时的同一判断在新证据下的重演——
架构合同挡住我,是它在履职。

## 试点暴露的其余三个隐性耦合

1. **测试用 `scripts.` 包路径导入脚本**:`from scripts.build_…_v1013
   import main`。首版脚本 shim 用裸名导入(只在直接执行时可用),
   包路径导入当场炸。修:双路径 try/except(镜像 check 脚本家族的
   `scripts._bootstrap` 惯用法)。
2. **测试互相导入**(共享 helper):`test_…_v1013` 从
   `tests.test_…_v1011` 拿 `ready_receipt_inputs`。测试不能上 shim
   ——re-export 会让 pytest 把同一批测试函数收集两遍——所以测试重命名
   必须同批改写其消费者(全库 grep 出 2 处,当场改)。
3. **字符串里的长名是合法的**:被迁模块内部的产物文件名常量
   (`…_v1013.json` 等)带着历史长名——那是输出契约,不许动。
   收口断言从"文件里不得再有长 stem"收窄为"不得再有 `minigpt.长stem`
   的 import 形态";对批外家族成员(v1010/v1011/constants)的长名
   import 保留原样——它们没被迁,直接可达。

## 度量与棘轮:shim-aware 定义

一个没被察觉就会让棘轮失灵的细节:shim 文件本身留在扁平目录里,
flat_dir_file_count 数它就永远不降。本版把度量改为 **shim-aware**:
`_is_shim`(AST:除 docstring 外只有 import 和一条 sys.modules 下标赋值)
的文件不算扁平居民、不算长名存量;同时 dup_def_stock 改成**递归**扫描
——被迁进子包的模块继续背着它的重复函数体计数,搬家不能"洗掉"重复债。
基线在新定义下重冻结并首次拧紧:

| 指标 | v1293 冻结 | 本版 |
|---|---|---|
| flat_dir_file_count | 1355 | 1355(重命名不动扁平数;降它属于规范化线) |
| long_name_stock | 282 | **276** |
| max_stem_length | 202 | **193** |
| dup_def_stock | 227 | 227(定义改递归,值不变) |

## 验证

- 试点 4 个测试文件 21/21(含未迁的 v1015 测试——它经 shim 消费旧
  路径,是转发正确性的活体证明);importlib 双路导入 `old is new` ✓。
- ratchet 测试扩到 5 个(新增:病理名 shim 不计入扁平/长名、迁走的
  重复体仍被递归计数);静态门 status=pass / new=0;elegance ratchet
  在新基线上 pass;全量套件另行背书(数字见提交信息)。
- git mv 保历史;产物文件名常量逐字节未动。

## 工程教训

1. **试点批的产出是"耦合清单",不是那 6 个文件**:三个隐性耦合
   (scripts. 包导入、测试互导、字符串长名)每一个都会在 90+ 文件的
   正式批里放大成灾;在 12 个文件上各花五分钟修一次,模式就稳了。
2. **棘轮要和迁移语义共同设计**:shim-aware + 递归 dup,缺一个,
   指标就会奖励错误的行为(囤 shim 不降数,或搬家洗重复)。
3. **测试是最诚实的消费者**:两处测试互导靠全库 grep 找齐;
   "0 处批外源码改动"的原则对测试放宽为"显式改写消费者",
   因为测试没有兼容面,shim 反而有害。

产物:6 个模块原地短名化 + 6 个长名 shim、
3 个脚本 shim(双路径);3 个测试重命名 + 2 处消费者改写;
elegance_ratchet shim-aware 化 + 基线首次拧紧。后续批复制此模式:
每批 ~30-60 文件,批批全套件 + CI 绿、棘轮拧紧一格。
