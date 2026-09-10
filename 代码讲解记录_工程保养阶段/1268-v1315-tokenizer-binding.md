# v1315：让 checkpoint 和 tokenizer 不能悄悄错配

## 一、问题从哪里来

v1313 把训练中真正影响随机轨迹的状态保存进了 checkpoint，v1314 又保证一次失败的磁盘写入不会摧毁上一份完整存档。两版之后，恢复入口已经能读回“哪一刻”和“怎样继续随机采样”。但还有一个更隐蔽的前提：checkpoint 中 embedding 行的编号，必须仍然对应同一份 tokenizer 的 token 含义。

原来的恢复代码只比较 `config.vocab_size` 和 tokenizer 的词表大小。这能发现词表增删，却发现不了两个 token 在 `itos` 中交换位置的情况。模型参数维度完全相同，`load_state_dict` 也会成功，训练甚至可以正常打印 loss；只是输入字符被映射到另一行 embedding，输出 id 解码时也会使用另一种含义。它不是“程序崩溃”，而是更危险的静默错配。

本版只增加一个工程护栏：新写的 checkpoint 记录 tokenizer 语义指纹，续训加载时在建模之前核对。科学实验的文本、损失、采样、判定逻辑和历史缓存都不改；旧 checkpoint 没有这个字段时继续按原路径加载，但不会凭空获得过去没有保存的身份信息。

## 二、为什么不能直接 hash 文件字节

最简单的方案是对 `tokenizer.json` 原始字节做 SHA-256。它会把缩进、键的排列、换行风格都当成 tokenizer 身份的一部分。一个用户只想重新格式化 JSON，或者不同系统写出了不同换行，模型就会被错误地拒绝。反过来，如果只 hash 词表长度，又回到了本版要修的漏洞。

因此指纹建立在加载后的语义对象上，而不是文件外观上。字符 tokenizer 的有效内容是类型、按顺序排列的 `itos` 和 unknown token；BPE 还必须加入按训练顺序排列的 merge 规则。`stoi` 是从 `itos` 派生出来的反向表，不另存一份可重复的顺序，避免同一语义因为派生缓存的表达不同而产生两个身份。规范 payload 使用固定 schema 版本、排序键和紧凑 JSON，再计算 SHA-256。

这里的版本字段不是项目包版本，也不是发布标签。它只标识指纹 payload 的解释方式。以后如果 tokenizer 语义增加特殊 token 或规范化配置，可以增加 schema 版本并设计迁移；本版不把未来格式提前猜进当前实现。

## 三、新模块的边界

`src/minigpt/training/tokenizer_binding.py` 只有两个职责函数。`tokenizer_digest` 把已加载的 tokenizer 转成稳定的语义 payload 并返回十六进制摘要；`validate_tokenizer_binding` 只在 checkpoint 中存在 `tokenizer_sha256` 时检查它。字段缺失直接返回，保持旧格式兼容；字段存在但不是字符串，或与当前 tokenizer 摘要不同，都抛出明确的 `ValueError`。

这个模块不读取路径、不打开 checkpoint、不初始化模型，也不修改 tokenizer。这样测试可以直接构造字符和 BPE 对象验证语义边界，训练入口也只需要在保存时计算一次，在加载时调用一次。`train.py` 仍负责参数和训练流程；新模块不成为另一个 CLI 或第二套 checkpoint 格式。

## 四、保存时绑定什么

训练完成后，原有 checkpoint 字典仍包含模型、优化器、随机状态、配置和步数。本版只多出 `tokenizer_sha256` 一个字符串。它来自当前内存中的 tokenizer，而不是重新打开输出目录中的 JSON，因此保存操作使用的对象和实际训练输入是同一个对象。v1314 的安全保存函数负责把整个字典写到候选文件并替换正式文件，本版不改变它的时序。

保存绑定的是 tokenizer 的语义，不是当前数据文件的摘要。相同 tokenizer 可以用于不同文本实验，反之同一词表大小也可能代表完全不同的 token 编号。把数据身份混进这个字段会扩大本版范围，且无法解决评估安排、学习率和优化器超参数的兼容问题，所以明确不做“所有训练配置指纹”。

## 五、恢复时必须尽早拒绝

`load_resume_state` 先用现有 `torch.load` 读取 checkpoint，再加载同目录 tokenizer。新校验紧接在 tokenizer 加载之后、`GPTConfig` 和模型实例化之前。这样同大小交换会在最早的业务边界失败，调用者看到的是“Checkpoint tokenizer binding mismatch”，而不是几十行之后的权重形状错误或训练一轮后的异常 loss。

训练入口在调用恢复函数之前虽然会根据参数准备文本，但它不会创建输出目录；恢复函数抛错后，后续的 model、optimizer、history 和 checkpoint 保存都不会执行。集成测试在交换词表后记录整个临时根目录的文件字节，并把新的输出目录放在另一路径，要求拒绝发生后没有新文件，也没有改写原 run 的文件。

## 六、字符 tokenizer 的故障测试

测试先用真实的 tiny checkpoint 走一遍训练入口，让新 checkpoint 真的带上摘要。随后只交换 JSON 中两个同样存在的 token。词表长度不变，配置维度不变，旧实现会继续训练；新实现计算出不同摘要并在恢复阶段拒绝。这个红灯对比保护的是“发现同大小 ID 置换”，而不是“发现词表长度变化”这种已经存在的检查。

另一个断言把 tokenizer JSON 解析后以不同键顺序和紧凑格式重新写出。重新加载的对象摘要必须不变，带有正确摘要的 checkpoint 也必须通过。这样可以证明算法绑定的是语义内容，而不是测试恰好保留了原文件的空格和排列。格式稳定性和错配敏感性是两个方向，缺一都会让摘要变得不实用或不可靠。

## 七、BPE 不能只测词表

BPE 的 token id 还依赖 merge 规则的先后。相同的初始字符和相同的最终 token 列表，合并顺序不同，编码一段文本时可能在不同位置优先合并，得到不同 id 序列。因此测试构造一个有重复 pair 的小 BPE tokenizer，保存原摘要，再把 merges 列表反转。反转后的对象词表长度仍相同，却必须得到不同摘要，并被 `validate_tokenizer_binding` 拒绝。

测试使用公开的 dataclass 字段构造变化对象，不依赖训练随机性，也不运行长实验。它只证明语义函数包含了 merge 顺序。生产入口当前默认可以使用 char 或 bpe，保存函数对两者使用同一字段名；摘要内部通过 tokenizer 类型区分是否加入 merges，不再给每种 tokenizer 建第三套保存代码。

## 八、旧 checkpoint 的兼容策略

仓库中有历史测试 fixture 和用户可能已经保存的 checkpoint，它们没有 `tokenizer_sha256`。如果把字段改成必填，升级工程工具就会让旧实验无法读取；如果遇到缺失字段悄悄伪造一个摘要，又会给人“已验证身份”的错误印象。本版选择显式兼容：字段缺失时保持原有加载行为，文档说明它没有追溯身份保证；新保存出来的 checkpoint 才开始带绑定。

兼容测试仍然通过 v1313 的旧格式删除字段测试，确认它能继续推进训练。新测试只对“字段存在”的 malformed 或 mismatch 做 fail-closed。这样两种事实不会混在一起：历史文件可用，但可信边界较窄；新文件具备额外的配对证明。版本说明和机器摘要分别记录这项边界，不能把兼容性包装成旧文件也有摘要。

## 九、它不是什么安全签名

SHA-256 只是一种稳定的内容摘要。若攻击者同时修改 checkpoint 中的摘要和 tokenizer 文件，二者仍可能重新匹配；本版没有密钥、证书或可信来源。因此字段名虽然使用 `sha256`，解释中必须称作 accidental-pairing guard，而不是防篡改签名。checkpoint 本身仍按现有 torch.load 信任边界处理。

同理，这个摘要不检查 source data、train/val 划分、batch size、学习率、评估间隔、硬件或 PyTorch 版本。v1313 已经在相同确定性环境中保护随机序列；本版只是把 tokenizer 这个独立前提也变成可检查字段。想要完整实验复现仍需要数据、参数和运行环境共同固定。

## 十、与 v1314 安全保存的衔接

新字段会随 checkpoint 字典一起交给 `save_checkpoint`。如果序列化或替换失败，v1314 保证上一份带有旧摘要的完整文件不被破坏；如果保存成功，新的模型状态和当前 tokenizer 摘要一并发布。两版职责分开：本版回答“这份权重对应哪个 tokenizer”，上一版回答“写入失败时哪份文件仍可读”。没有把 tokenizer JSON 本身塞进 checkpoint，也没有改动原子替换函数。

失败恢复测试因此检查三件事：交换 tokenizer 时先拒绝且不创建新输出；保存故障时旧 checkpoint 字节和 tokenizer 字节都保留；正常重试后新 checkpoint 可加载并带摘要。它们分别属于绑定、写入和训练链路，不能用一个 happy-path load 测试代替全部证明。

## 十一、验证门和最强质疑

本版的红灯是旧实现对同大小 token 交换不报错。绿灯定向测试包含 31 个用例，覆盖摘要格式稳定性、BPE merge 顺序、真实训练保存、拒绝前无输出，以及上一版随机续跑和 checkpoint 写入测试。Ruff、严格 mypy、全部快速 CI 与原覆盖率门必须继续通过；不修改 baseline、floor、科学 verdict 或旧 fixture。

最强质疑是“摘要真的覆盖了所有影响训练的条件吗？”答案是否定的，而且这是诚实边界。它覆盖 tokenizer 语义这一项，故意不覆盖数据和训练超参；把范围写窄并配套拒绝错配，胜过制造一个名字很大的“全配置指纹”却漏掉关键字段。另一个质疑是“旧 checkpoint 为什么不拒绝？”因为它没有信息可验证；兼容和可证明性必须同时写清。

## 十二、独立复核与一句话总结

运行 `python -B -m unittest tests.test_tokenizer_binding tests.test_checkpoint_io tests.test_rng_state tests.test_resume_rng -v` 可复核本版与前两版的关键链路。完整覆盖率仍使用 `python -B scripts/run_test_coverage.py --out-dir runs/test-coverage --fail-under 88.98`，机器摘要保存实际测试数、覆盖率和 21 个快速门结果。发布时只暂存明确文件，验证脚本和工具目录在收尾删除。

一句话总结：v1315 把 tokenizer 的真实语义绑定到新 checkpoint，让同大小但含义已变的词表错配在训练开始前失败，而不是悄悄制造另一条实验轨迹。
