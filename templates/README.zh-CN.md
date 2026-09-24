# 模板

[English](README.md) | [简体中文](README.zh-CN.md)

这些文件是 RAES 里“怎么写”的那一层。它们为操作手册里的每一类文件提供固定结构：计划 memo、纳入标准、codebook、审计设计以及 prompt。每个 `{{...}}` 占位符都代表研究者要做的一个决定；占位符旁边的例子是一种填法，取自我的项目，不是必须照做的。带占位符的骨架文件可以通过草稿检查，但故意无法通过 `--ready` 检查。

一份中文指南逐个文件、逐个字段地说明怎么填：[模板填写指南](GUIDE.zh-CN.md)。

## 新建一个项目

在 RAES 文件夹下运行，并将目标目录设为仓库外的一个新文件夹：

```sh
python tools/new_project.py ../my-evidence-project
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
```

第一条命令会创建项目所需的各个文件夹（每个文件夹下都附有一份简短的 README），并把模板复制进去，同时复制属于该项目的三个程序：去重脚本、筛选程序以及流程运行程序。该命令还会根据 codebook 输出两份列名清单（全部列，以及由执行模型填写的列），并把复制进去的每个模板记进 `raes_templates.json`；后续运行 `python tools/check_templates.py --project <project>` 时，就能据此识别出哪些文件还是旧版模板的副本、而且还没有填写过。第二条命令检查 codebook，并列出尚未填写的占位符。纳入标准文件从第一天起就可以单独检查：`python tools/check_codebook.py --eligibility ../my-evidence-project/codebook/eligibility.json`。

当 codebook 编写完毕并获得批准后，将 `status` 设为 `ready`，记录批准信息，把 `eligibility.json` 的 SHA-256 哈希填入 codebook，然后运行：

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

无需安装任何包。在 Windows 上，用你平时用的 Python 启动器。

## 需要填写的内容

下表各行按照流程的先后顺序排列。每个调用 AI 的阶段各写一份计划 memo。

| 文件 | 阶段 | 包含内容 |
|---|---|---|
| [eligibility.json](eligibility.json) | 目标与纳入标准（S0）；供后续所有阶段读取 | 纳入标准，带编号，每条附有澄清。整个项目共用这一份文件 |
| [search/dedup_rules.json](search/dedup_rules.json) | 去重（S2），只在不用文献管理软件、改用 skill 的去重脚本时需要 | 记录如何比对、重复时保留哪个来源的那一条、用哪些标签标记预印本、哪些记录对交由研究者判断，以及在筛选前剔除哪些文献类型 |
| [screening/screening_rules.md](screening/screening_rules.md) | 筛选（S3、S4） | 文字形式的筛选规则：每条标准对应一条规则、各阶段的判断逻辑、运行前的检查项、版本变更记录 |
| [screening/screen_rules_template.py](screening/screen_rules_template.py) | 筛选（S3、S4） | 同一套规则的可运行程序版本：每条标准一组词表，每条记录一个判断和理由，按每条标准给出的证据供审计使用 |
| [plan_memo.md](plan_memo.md) | 凡是调用 AI 的阶段：筛选审计（S5）、编码（S8）、编码审计（S9），以及由模型承担时的筛选阶段（S3、S4） | 一个阶段的计划：这一步回答什么问题、判断单位、输入和输出、模型能看什么和不能看什么、试跑、怎样才算完成、批准 |
| [validation/screening/](validation/screening/memo.md) | 筛选审计（S5） | 筛选审计的一整套文件：memo、审计 codebook、配置文件以及两个 prompt。全文模式，例如两个主审计模型，意见不一致时加第三个；摘要模式，例如一个审计模型，它给出的“保留”只是候选，还要过冻结的全文筛选 |
| [codebook.json](codebook.json) | 编码（S8） | 各变量的定义：类型、是否允许空值、字段由谁填写（执行模型还是程序）、编码规则、允许引用的证据、值缺失时怎么办、示例与反例。随后是结果指标对应表、配对、汇总与方向规则、来源优先级以及 worked cases |
| [prompts/](prompts/coding_system.md) | 编码（S8） | 编码用的 system prompt 和 paper prompt（针对每篇论文的 prompt） |
| [validation/coding/](validation/coding/memo.md) | 编码审计（S9） | 编码审计的一整套文件：memo、审计 codebook、配置文件以及两个 prompt。例如由一个审计模型检查每篇论文，每一处质疑由盲审的裁决者处理 |
| [project/](project/README.md) | 全部阶段 | 新建项目文件夹的初始文件，包含附带 `pipeline.json` 的 `run_pipeline.py`：一条命令重跑所有由程序完成的阶段，并把每个输出和正式输出比对 |

筛选程序是一个骨架，思路和 Robleto and Shehadeh (2025) 一样：先改文件开头的词表，使每个条目与 `eligibility.json` 中的相应标准一一对应；接着拿已知应当纳入的论文测试；最后确定版本并冻结。运行 `python templates/screening/screen_rules_template.py --help` 可以查看两个阶段的用法。题目摘要审计确认的记录写进一份冻结清单，用 `--after-ta-audit` 进入全文阶段；全文阶段还会核对：此前的题目摘要运行是否恰好覆盖当前记录文件中的全部记录。

变量骨架用各组（arm）层面的效应量输入（均值、SD、N、事件数、总数）作为示例。请删去不适用的部分并注明原因。不要因为模板展示了这些结果指标就照搬添加。`columns` 按顺序列出所有变量；执行模型的列名清单则去掉所有由程序负责的字段。`Row_UID`、`g`、`SE_g` 以及置信区间始终由程序生成。

`worked_cases` 包含三个具体示例：一个正例、一个缺失数据的例子和一个边界例子。检查器要求它们存在，但不评判内容。评判内容是试跑的事。

## 确保各处的标准完全一致

纳入标准只放在一个文件里。codebook 不抄录它们的文字，而是记录该文件的 SHA-256 哈希值；这个哈希按文件的原始字节计算，换行符也算在内：

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
```

将计算出的哈希值填入 codebook 的 `eligibility.sha256` 字段中。这样一来，筛选、编码、数据准备以及每一次审计使用的都是同一份文本。一旦标准发生变更，哈希值就会改变。正确的做法是升一个版本，并写明它影响哪些地方，而不是只换一个哈希值。

## 生成 prompt

生成器直接读取 codebook 和纳入标准文件的原文，并根据 codebook 中的字段归属生成执行模型的列名清单；这些内容代入模板的占位符，context 文件不能覆盖它们。运行前把生成好的 prompt 连同哈希一起冻结：这样可以检测之后对生成文件的修改；生成器本身无法阻止这类修改。context 文件只提供模板所要求的字段（例如 `PAPER_ID` 和 `SOURCES_JSON`）；system prompt 的 context 文件就是 `{}`。

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

预览还没填完的 codebook，用 `--draft`。这条命令拒绝覆盖已有的输出文件，也不向任何地方发送内容。审计 prompt 和它所属的那套审计文件一起放在 `validation/` 目录下；编码审计模型和裁决者共用同一份审计 codebook，且裁决者绝不会看到审计模型提出的值。

## 检查器能做什么、不能做什么

检查器识别 `raes-codebook/1` 这种结构。它会验证必需的小节是否存在、变量和列名是否一致、示例是否符合其类型与取值范围、缺失值规则与字段归属规则是否已声明、标准编号能否对应上，以及纳入标准的哈希是否匹配。它不判断规则在科学上对不对、样本够不够大、证据是不是真的。这些仍需由研究者判断。

[虚构示例中填好的 codebook](../examples/synthetic/inputs/codebook.json) 展示了一个完整的小型范例。其中的批准记录属于虚构内容，不要把它照抄成真实的批准。
