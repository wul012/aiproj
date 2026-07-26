# 1265 - v1308 core 包原子迁移:扁平计数 1,355 → 1,350(该指标史上第一次下降)

## 本版目标与不做什么

v1307 的负结果给出了明确的下一步:**整包原子迁移**,而 core 的前置
条件是拆分 299 行的 `model.py`。本版按那份设计逐条执行:先验
checkpoint 兼容,再拆 model,再整包搬迁,最后改契约。不做什么:
不碰其他 owner 包(training/evaluation/serving/reports/governance);
不改任何模型数学。

## 第 1 步:checkpoint 兼容性闸门(必须先过)

设计文档把这条列为**动手前的硬闸门**:如果 `.pt` 里 pickle 了
`GPTConfig`/`MiniGPT` 对象本身,类的模块路径就被烘进了文件,拆分会让
既有产物**加载不了**。

用 `pickletools` 直接读 pickle 的 opcode(不执行载荷)扫描两个
checkpoint,包括 v1185 那个 canonical grok checkpoint:

```
minigpt class refs: NONE
other globals: collections.OrderedDict, torch.FloatStorage,
               torch._utils._rebuild_tensor_v2
```

只有 state_dict 与普通元数据,**没有任何 minigpt 类路径**。闸门通过。
并且记下**不变量**:18 个张量,`STATE_SHA256 = 7b4b9761...`,迁移
前后必须逐位相同。

## 第 2 步:沿自然接缝拆 model.py

347 行的 model.py 有一条清晰的接缝:

- `core/layers.py`(165 行):`GPTConfig` / `CausalSelfAttention` /
  `MLP` / `Block`——积木
- `core/model.py`(207 行):`select_next_token` / `MiniGPT`——模型本体,
  并**再导出 `GPTConfig`**,使 `from minigpt.model import GPTConfig`
  这类历史写法一字不改地继续可用

两者都在 owner 包 220 行上限之下。定义体**逐字节照搬**,只换了家。

## 第 3 步:整包原子搬迁

五个原语(model / tokenizer / dataset / history / rope)**一次全搬**,
扁平路径留 `sys.modules` 转发 shim。因为 shim 被优雅棘轮排除在
`flat_dir_file_count` 之外,指标**恰好下降 5**:**1,355 → 1,350**。
这是该指标自 v1293 冻结以来的**第一次下降**。

v1307 的循环导入没有复发:`core/*` 内部只互相引用(model → layers →
rope),不再有任何回指扁平命名空间的门面。

## 抓到的坑:装饰器不在 `node.lineno` 里

第一次搬迁后 `test_attention` 报 `GPTConfig() takes no arguments`。
根因是切片提取:`ast` 节点的 `lineno` 指向 `class`/`def` 关键字本身,
**不包含装饰器行**,于是 `@dataclass` 被静默丢掉,`GPTConfig` 退化成
普通类。修法是取 `min(node.lineno, 各 decorator.lineno)`,并断言取出的
文本以 `@` 开头。教训:**AST 切片必须显式处理装饰器**——丢掉的东西
不会报语法错,只会在运行期以"构造函数签名变了"这种形式现形。

发现后完整回滚、修工具、重跑,而不是就地打补丁。

## 契约变更(并附等价强度补偿)

完成迁移必然退役"子模块只能是门面"——那正是 `transitional` 一词预告的
终点。替代规则保证守卫总强度不降:

- 门面形制规则改按**形状**判定(而非位置),facade 与实现可以在同一个
  包里共存;
- 实现子模块继续受**不变的 220 行上限**与**不变的分层禁令**约束;
- **新增**:实现子模块不得再从它被迁出的那片扁平命名空间导入——
  这正是 v1307 循环导入的成因,现在被测试挡住。

## 数字

| 指标 | 迁移前 | 迁移后 |
|---|---|---|
| flat_dir_file_count | 1,355 | **1,350** |
| core 包最大模块 | 4 行(门面) | 207 行(实现,上限 220) |
| checkpoint STATE_SHA256 | 7b4b9761... | **7b4b9761...**(逐位相同) |
| core 相关测试 | — | 28/28 |
| 21 个闸门 | — | 全绿 |

## 工程教训

1. **负结果的设计文档能直接被执行**:v1307 停在"文档 + 零代码",本版
   只是照着第 1→2→3 步走,没有一次返工是因为方向错。前一版的克制
   换来了这一版的直达。
2. **硬闸门要在动手前跑**:checkpoint 兼容性如果留到最后再验,拆分
   已经发生,发现问题就是回滚整版。闸门的价值在于它的**位置**。
3. **不变量要用哈希钉死**:`STATE_SHA256` 让"没弄坏模型"从主观判断
   变成一行可复核的证据。

产物:`core/layers.py` + `core/model.py`(拆分,均 ≤220 行),五个原语
实现迁入 core,扁平路径留 shim;架构契约完成"过渡期"演进;优雅基线
flat_dir_file_count 拧紧至 **1,350**。剩余:另外五个 owner 包,以及
~500 个逐版本生成的治理产物模块(迁移 vs 归档出 src,产品决定)。
