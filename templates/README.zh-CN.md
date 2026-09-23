# 模板

[English](README.md) | [简体中文](README.zh-CN.md)

这些文件是 RAES 里“怎么写”的那一层。它们给操作手册里的每一类文件一个固定的形状：计划 memo、纳入标准、codebook、审计设计和 prompt。每个 `{{...}}` 都是一个要由研究者做的决定；占位符旁边的例子是一种填法，取自我的项目，不是必须照做的。带占位符的骨架能通过草稿检查，但故意通不过 `--ready` 检查。

逐个文件、逐个字段的填写说明见[模板填写指南](GUIDE.zh-CN.md)。

## 新建一个项目

在 RAES 文件夹下运行，目标要选仓库之外的一个新文件夹：

```sh
python tools/new_project.py ../my-evidence-project
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
```

第一条命令建好项目的各个文件夹，每个里面放一份简短的 README，把模板复制进去，同时复制进去的还有属于项目自己的三个程序：去重脚本、筛选程序和流水线运行程序。它从 codebook 生成两份列名清单（全部列，以及由执行模型填写的列），并把复制的每个模板记进 `raes_templates.json`；以后用 `python tools/check_templates.py --project <项目>` 就能看出哪些文件还是没填过的旧模板。第二条命令检查 codebook，列出还没填的占位符。纳入标准文件从第一天起就可以单独检查：`python tools/check_codebook.py --eligibility ../my-evidence-project/codebook/eligibility.json`。

codebook 填完并经过批准后，把 `status` 设为 `ready`，记录批准信息，把 `eligibility.json` 的 SHA-256 填进 codebook，然后运行：

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

不需要任何第三方包。Windows 上用你平时用的 Python 启动器即可。

## 要填的文件

按流程的先后排列。计划 memo 在每个调用 AI 的阶段各写一份。

| 文件 | 用在哪个阶段 | 内容 |
|---|---|---|
| [eligibility.json](eligibility.json) | 目标与纳入标准（S0）；之后每个阶段都读它 | 纳入标准，带编号，每条附澄清。整个项目只有这一个文件 |
| [search/dedup_rules.json](search/dedup_rules.json) | 去重（S2）；只在不用文献管理软件、改用 skill 的去重脚本时需要 | 记录怎么配对、重复时保留哪个来源的那一条、哪些标签表示预印本、哪些配对交给研究者决定、筛选前按文献类型去掉哪些 |
| [screening/screening_rules.md](screening/screening_rules.md) | 筛选（S3、S4） | 用文字写的筛选规则：每条标准一条规则、两个阶段各自的判定逻辑、运行前的检查、版本记录 |
| [screening/screen_rules_template.py](screening/screen_rules_template.py) | 筛选（S3、S4） | 同一套规则的可运行程序：每条标准一组词表，每条记录一个判断和理由，逐条标准的证据供审计使用 |
| [plan_memo.md](plan_memo.md) | 任何调用 AI 的阶段：筛选审计（S5）、编码（S8）、编码审计（S9）；如果由模型做筛选，也包括筛选（S3、S4） | 一个阶段的计划：问题、判断单位、输入和输出、模型能看什么和不能看什么、试跑、完成标准、批准 |
| [validation/screening/](validation/screening/memo.md) | 筛选审计（S5） | 筛选审计一整套：memo、审计 codebook、配置和两个 prompt。全文模式，例如两位主审加一位第三位；题摘模式，例如一位审计者，它的“保留”是候选，要经过冻结的全文筛选 |
| [codebook.json](codebook.json) | 编码（S8） | 变量：类型、能否为空、由谁填（执行模型还是程序）、规则、允许的证据、缺失时怎么办、例子和反例。之后是结果指标对应表、配对规则、合并规则、方向规则、来源优先级和 worked cases |
| [prompts/](prompts/coding_system.md) | 编码（S8） | 编码的 system prompt 和 paper prompt |
| [validation/coding/](validation/coding/memo.md) | 编码审计（S9） | 编码审计一整套：memo、审计 codebook、配置和两个 prompt。例如一位审计者检查每篇论文，每处质疑由盲审的裁决者处理 |
| [project/](project/README.md) | 全部 | 新项目文件夹的起始文件，包括 `run_pipeline.py` 和 `pipeline.json`：一条命令重跑所有由程序完成的阶段，并把每个输出和正式输出比对 |

筛选程序是一个骨架，思路和 Robleto and Shehadeh (2025) 一样：改文件开头的词表，让每一项对应 `eligibility.json` 里的一条标准；先在你已知应该纳入的论文上试，再定版本冻结。`python templates/screening/screen_rules_template.py --help` 显示两个阶段的用法。题目摘要审计确认的记录写进一份冻结清单，用 `--after-ta-audit` 进入全文阶段；全文阶段还会核对题目摘要那次运行是否恰好覆盖了它拿到的记录文件。

变量骨架以实验组层面的效应量输入（均值、SD、N、事件数、总数）为例。不适用的删掉，并写明原因。不要因为模板里有某个结果指标就增设它。`columns` 按顺序列出全部变量；执行模型的列表去掉所有由程序负责的字段。`Row_UID`、`g`、`SE_g` 和置信区间永远由程序填写。

`worked_cases` 是三个写出来的例子：一个正例、一个数据缺失的例子、一个边界情形。检查器要求它们存在，但不评判内容。评判内容是试跑的事。

## 让纳入标准处处一致

纳入标准只放在一个文件里。codebook 不抄它的文字，而是记录这个文件的 SHA-256，按文件的实际字节计算，换行符也算在内：

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
```

把哈希填进 codebook 的 `eligibility.sha256` 字段。这样筛选、编码、数据准备和每一次审计用的都是同一段文字。标准一改，哈希就变。正确的做法是升一个版本并写明影响范围，而不是只换一个哈希。

## 生成 prompt

生成器自己读取 codebook、纳入标准文件和执行模型的列名，所以 prompt 里是这些文件的原文，context 文件覆盖不了它们。运行前把生成好的 prompt 连同哈希一起冻结：之后有人改了生成的文件就能查出来，这一点生成器本身防不住。context 文件只提供模板额外需要的字段，比如 `PAPER_ID` 和 `SOURCES_JSON`；system prompt 不需要额外字段，context 就是 `{}`。

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

预览还没填完的 codebook 用 `--draft`。这条命令不覆盖已有的输出文件，也不向任何地方发送内容。审计用的 prompt 和各自的审计套件放在一起，在 `validation/` 下；编码审计者和裁决者共用一份审计 codebook，裁决者永远看不到审计者提出的值。

## 检查器能做什么、不能做什么

检查器认识 `raes-codebook/1` 这种结构。它核对必需的章节、变量和列名是否一致、例子是否符合类型和范围、缺失规则和归属是否声明、标准编号能否对应、纳入标准的哈希是否匹配。它不判断规则在科学上对不对、样本够不够大、证据是不是真的。这些仍然是研究者的事。

[合成例子里填好的 codebook](../examples/synthetic/inputs/codebook.json) 是一个完整的小例子。它的批准记录是虚构的，不能照抄成真实的批准。
