# 模板

[English](README.md) | [简体中文](README.zh-CN.md)

这些文件是 RAES 里"怎么写"的那一层。它们给操作手册里的每一类文件一个固定的形状：计划 memo、纳入标准、codebook、验证设计和 prompt。每个 `{{...}}` 都是一个要由研究者做的决定。带占位符的骨架能通过草稿检查，但故意通不过 `--ready` 检查。

## 新建一个项目

在 RAES 文件夹下运行，目标要选仓库之外的一个新文件夹：

```sh
python tools/new_project.py ../my-evidence-project
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
```

第一条命令建好项目的各个文件夹，每个里面放一份简短的 README，把模板复制进去，并从 codebook 生成两份列名清单：全部列，以及由执行模型填写的列。第二条命令检查 codebook，列出还没填的占位符。

codebook 填完并经过批准后，把 `status` 设为 `ready`，记录批准信息，把 `eligibility.json` 的 SHA-256 填进 codebook，然后运行：

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

不需要任何第三方包。Windows 上用你平时用的 Python 启动器即可。

## 按什么顺序填

| 文件 | 内容 |
|---|---|
| [plan_memo.md](plan_memo.md) | 一个阶段的计划：问题、判断单位、输入和输出、模型能看什么和不能看什么、试跑、完成标准、批准 |
| [eligibility.json](eligibility.json) | 纳入标准，带编号，每条附澄清。整个项目只有这一个文件 |
| [codebook.json](codebook.json) | 变量：类型、能否为空、由谁填（执行模型还是程序）、规则、允许的证据、缺失时怎么办、例子和反例。之后是结果指标对应表、配对规则、合并规则、方向规则、来源优先级和 worked cases |
| [validation_memo.md](validation_memo.md) | 一次审计的设计：目标、抽样框、单位、全查还是抽样、分层和种子、停止规则、每位审计者能看什么、分歧怎么流转、怎样报告 |
| [validation_codebook.json](validation_codebook.json) | 审计者遵守的规则。一个文件覆盖筛选审计、编码审计和裁决，各为一种模式 |
| [validation_config.json](validation_config.json) | 一次审计的运行设置：抽样框、模型、抽样、流转、重试、预算。文件填完并批准之前，不发出真实请求 |
| [prompts/](prompts/coding_system.md) | 五个 prompt 模板：编码的 system prompt、编码的 paper prompt、编码审计、裁决、筛选审计 |
| [project/](project/README.md) | 新项目文件夹的起始文件 |

变量骨架以实验组层面的效应量输入（均值、SD、N、事件数、总数）为例。不适用的删掉，并写明原因。不要因为模板里有某个结果指标就增设它。`columns` 按顺序列出全部变量；执行模型的列表去掉所有由程序负责的字段。`Row_UID`、`g`、`SE_g` 和置信区间永远由程序填写。

`worked_cases` 是三个写出来的例子：一个正例、一个数据缺失的例子、一个边界情形。检查器要求它们存在，但不评判内容。评判内容是试跑的事。

## 让纳入标准处处一致

纳入标准只放在一个文件里。codebook 不抄它的文字，而是记录这个文件的 SHA-256，按文件的实际字节计算，换行符也算在内：

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
```

把哈希填进 `eligibility.sha256`。这样筛选、编码、数据准备和每一次审计用的都是同一段文字。标准一改，哈希就变。正确的做法是升一个版本并写明影响范围，而不是只换一个哈希。

## 生成 prompt

生成器自己读取 codebook、纳入标准文件和执行模型的列名，所以没有人能在 prompt 里手动改动它们。context 文件只提供模板额外需要的字段，比如 `PAPER_ID` 和 `SOURCES_JSON`；system prompt 不需要额外字段，context 就是 `{}`。

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

预览还没填完的 codebook 用 `--draft`。这条命令不覆盖已有的输出文件，也不向任何地方发送内容。审计者和裁决者共用一份审计 codebook。裁决者收到被质疑的字段、原始的编码行和原始材料，永远看不到审计者提出的值。

## 检查器能做什么、不能做什么

检查器认识 `raes-codebook/1` 这种结构。它核对必需的章节、变量和列名是否一致、例子是否符合类型和范围、缺失规则和归属是否声明、标准编号能否对应、纳入标准的哈希是否匹配。它不判断规则在科学上对不对、样本够不够大、证据是不是真的。这些仍然是研究者的事。

[合成例子里填好的 codebook](../examples/synthetic/inputs/codebook.json) 是一个完整的小例子。它的批准记录是虚构的，不能照抄成真实的批准。
