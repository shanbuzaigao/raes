# 模板填写指南

[模板说明（English）](README.md) | [模板说明（简体中文）](README.zh-CN.md)

这份指南按文件、按字段说明每个模板该填什么，给读中文的人用。模板本身保持英文：prompt 和 codebook 是给模型读的，整个项目只保留一个版本；JSON 的字段名要和检查程序对得上。所以文件是英文的，解释在这里。

每个字段按同一格式写：**是什么、填什么、例**。例子按我的项目改写（一篇关于大语言模型在经典经济学博弈中如何行为的综述），做了简化，只示意填法，不是必须照做的。

各节按[操作手册](../PROTOCOL.zh-CN.md)的阶段排列。不必从头读到尾，做到哪一步查哪一节。

## 0. 开始之前

### 0.1 建项目

在 RAES 文件夹下运行，目标选仓库之外的一个新文件夹：

```sh
python tools/new_project.py ../my-evidence-project
```

（装了 `raes` skill 的人，也可以让 skill 代跑它自带的 `scripts/new_project.py`，效果一样。）

建好之后，模板落在这些位置：

| 项目里的文件 | 来自哪个模板 | 用在哪一步 | 本指南的节 |
|---|---|---|---|
| `codebook/eligibility.json` | `eligibility.json` | 目标与纳入标准（S0） | 1 |
| `screening/screening_rules.md`、`screening/screen_rules_template.py` | `screening/` | 筛选（S3、S4） | 2、3 |
| `plans/STAGE_PLAN.md` | `plan_memo.md` | 每个调用 AI 的阶段一份 | 4 |
| `validation/screening/`（memo、codebook、config、两个 prompt） | `validation/screening/` | 筛选审计（S5） | 5 |
| `codebook/codebook.json`，以及由它生成的 `codebook/columns.csv`、`codebook/executor_columns.csv` | `codebook.json` | 编码（S8） | 6 |
| `prompts/coding_system.md`、`prompts/coding_paper.md` | `prompts/` | 编码（S8） | 7 |
| `validation/coding/`（memo、codebook、config、两个 prompt） | `validation/coding/` | 编码审计（S9） | 8 |
| `README.md`、`CURRENT_STATUS.md`、`.gitignore`，以及程序生成的 `plans/DECISIONS.md` | `project/` | 全程 | 9 |

其余文件夹（`search`、`papers`、`table_build`、`analysis`、`releases`、`archive`）各带一份一句话的 README，说明放什么。

### 0.2 通用规则

- **占位符。** `{{...}}` 表示一个要由你决定的地方。把整段（连同花括号）换成你的内容。检查器把留下的 `{{` 当作还没做的决定；`TODO`、`TBD`、`REPLACE_ME` 也算。
- **例子不是答案。** 模板里 "e.g." 和 "for example" 后面的内容，以及本指南的"例"，都是我的项目的一种填法。你的项目按自己的情况填。
- **用英文写。** 文件里的内容用英文。英文写不顺，可以先写中文，让 AI 助手翻译，再自己逐句核对意思。
- **版本号。** 从 `0.1.0-draft` 开始。规则改了就升版本，写明改了什么、影响哪些记录；不回头改旧版本。
- **日期。** `YYYY-MM-DD`，例如 `2026-09-17`。
- **哈希（SHA-256）。** 很多文件要记录 `eligibility.json` 的 SHA-256。它是按文件的实际字节算出的一串 64 位十六进制数；文件改一个字符，它就变。这样每个阶段用的是不是同一份标准，一比就知道。算法：

  ```sh
  python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
  ```

- **两类占位符。** 大多数占位符由你填。但 prompt 文件里的 `{{RECORD_ID}}`、`{{ELIGIBILITY_JSON}}` 这一类是运行时由程序代入的，不要手填。指南里会分别标出。
- **数字字段。** JSON 里写着 `null` 的数字项，决定后填数字，不加引号，例如 `"seed": 20260917`。
- **几个英文用语。** TA = title and abstract，题目摘要阶段；FT = full text，全文阶段；executor = 执行模型，做编码的那个模型；auditor = 审计模型；adjudicator = 裁决模型；frame = 审计的总体，即要抽查的全部记录；stratum、strata = 分层；seed = 随机种子；snapshot = 一次检索的快照；near miss = 险些纳入的记录。

## 1. 纳入标准 `eligibility.json`（目标与纳入标准，S0）

整个项目只有这一个纳入标准文件。其他文件不抄它的文字，只记录它的哈希。

| 字段 | 是什么 | 填什么 |
|---|---|---|
| `version` | 这份标准的版本 | 起始 `0.1.0-draft`；标准一改就升版本 |
| `criteria[].id` | 标准编号 | `C1`、`C2`……筛选规则和审计 codebook 都用这个编号引用它，定了不要改 |
| `criteria[].text` | 一条标准 | 一句话，能逐条核对。写"什么算符合"，不写"相关研究"这类话 |
| `criteria[].clarifications` | 澄清 | 纳入、排除、拿不准的情形各举一例；什么证据算数；缺统计量不等于不纳入 |
| `mixed_condition_rule` | 一篇论文里既有符合的条件也有不符合的条件时怎么办 | 写清在哪一级判断（论文、实验还是实验条件）；不符合的条件跳过并记录，不因它们排除整篇 |

模板给了三条，按需增删。

**例**

```json
{
  "id": "C1",
  "text": "The study reports at least one classic economic game (prisoner's dilemma, trust, ultimatum, dictator, public goods, stag hunt or coordination game).",
  "clarifications": "Include: a new variant of a listed game with the same payoff structure. Exclude: video games and market experiments. Uncertain: a game used only as a warm-up task; keep for full-text reading."
}
```

（C1：研究至少报告一种经典经济学博弈。澄清里写了纳入、排除、拿不准各一例。）

`mixed_condition_rule` 例：`"Apply the criteria to each experimental condition. Code the eligible conditions and list each skipped condition with the criterion it failed."`（按实验条件逐个判断；符合的编码，不符合的记下来并注明是哪条标准不符合。）

## 2. 筛选规则 `screening/screening_rules.md`（筛选，S3、S4）

用文字写筛选规则。程序 `screen_rules_template.py`（第 3 节）是同一套规则的代码版。两边要一致：改一边就改另一边，并升版本。

**标题行**

| 占位符 | 填什么 |
|---|---|
| `{{PROJECT_ID}}` | 项目代号，与 codebook 的 `project.id` 一致。例：`llm-games` |
| `{{RULES_VERSION}}` | 规则版本，与程序里的 `RULES_VERSION` 一致。例：`0.1.0-draft` |
| `{{ELIGIBILITY_FILE_AND_SHA256}}` | 纳入标准文件的路径和哈希。例：`codebook/eligibility.json, sha256 7e8512…` |
| `{{SNAPSHOT_ID}}` | 这次筛选用的检索快照编号。例：`search-2026-09-01` |

**第 1 节 输入**

| 占位符 | 填什么 |
|---|---|
| `{{RECORD_FILE_AND_FORMAT}}` | 去重后的记录文件和格式。例：由 EndNote 导出文件转成的 `records.csv`，三列 `record_id`、`title`、`abstract` |
| `{{FIELDS}}` | 题目摘要阶段用到的字段。例：`record_id, title, abstract` |
| `{{EXTRACTION_TOOL_AND_VERSION}}` | 从 PDF 提取全文的工具和版本，全项目只用一个。例：`PyMuPDF 1.27` |
| `{{NOT_RETRIEVED_FILE_OR_NONE}}` | 取不到全文的记录清单文件，每行一个记录编号，运行全文阶段时用 `--not-retrieved` 传给程序；没有就写 `none`。例：`screening/not_retrieved.txt` |
| `{{TITLE_PHRASES_OR_NONE}}` | 在文献管理软件里按文献类型去掉的记录（这是 S2 做的事），没有就写 `none`。例：`titles containing "systematic review" or "meta-analysis"` |

**第 2 节 每条标准一条规则**

表格每列的填法：

| 列 | 填什么 |
|---|---|
| Criterion | 标准编号加简短标签，编号与 `eligibility.json` 一致。例：`C1 classic economic game` |
| Checked at | 在哪个阶段检查：`TA, FT`（两个阶段都查）、`TA` 或 `FT only` |
| Supporting terms or patterns | 出现哪些词或模式就算支持这条标准 |
| Blocking terms | 出现哪些词就算不符合；没有写 `none` |
| Supported when | 判定规则。例：`at least one supporting term and no blocking term` |
| Evidence recorded | 保留模板的写法 `matched term and surrounding text`（命中的词和上下文） |

`{{LIST_OR_NONE}}`：词表判断不了的标准，留给全文阅读，或留给按 codebook 筛选的模型。例：`whether the prompt steered the behaviour`（prompt 是否引导了行为）。

模板的表格下方已有一个标着 **Example** 的填好的表，来自我的项目，可以对照。

**第 3 节 判定逻辑**

`{{NEAR_MISS_DEFINITION}}`："险些纳入"的定义，筛选审计（S5）按它分层。例：`failed exactly one criterion`（只有一条标准不符合）。

**第 4 节 正式运行前的检查**

| 占位符 | 填什么 |
|---|---|
| `{{SHA256}}` | 记录文件冻结后的哈希 |
| `{{PILOT_SET_AND_RESULT}}` | 你事先知道应该纳入的论文，以及试跑结果。例：`12 known relevant papers; all kept at TA and FT under rules 0.1.0` |
| `{{COUNTS}}` | 各阶段的记录数，要能对上 PRISMA 流程图。例：`1,840 records; 312 kept at TA; 58 included at FT` |

**第 5 节 版本**

`{{CHANGE_LOG}}`：每次改动写改了什么、为什么、可能影响哪些记录。例：`0.1.1: added "prisoners' dilemma" to C1; can affect the TA decisions of the 2026-09 batch`。

## 3. 筛选程序 `screening/screen_rules_template.py`（筛选，S3、S4）

不用会写 Python。只改文件开头的两处。

- `RULES_VERSION`：与规则文档一致。
- `CRITERIA`：每条标准一项。键是标准编号（`"C1"`），与 `eligibility.json` 一致。

| 键 | 填什么 |
|---|---|
| `label` | 简短标签。模板里的三项标着 "(example)"，换成你自己的时去掉 |
| `any_of` | 支持词表：出现任意一个就算支持。程序不分大小写，但按整词匹配，所以单复数要分别列出（`"offer", "offers"`）；弯引号会被程序统一成直引号 |
| `none_of` | 阻断词表：出现任意一个就算不符合。没有写 `[]` |
| `check_at` | 哪个阶段检查：`["ta", "ft"]`、`["ta"]` 或 `["ft"]` |

模板里的三项（经典经济学博弈、生成式 AI 做决策、报告了行为结果）是例子，换成你自己的标准。词表判断不了的标准不写进程序。

**输入**

- `records.csv`：三列 `record_id`、`title`、`abstract`，去重（S2）后导出；`record_id` 不能空、不能重复。
- 全文阶段：`fulltext/<record_id>.txt`，每条被保留的记录一个文件，从 PDF 提取，全项目用同一个工具并记录版本。程序要求每条保留记录都有全文文件。确实取不到的，把记录编号写进一个清单文件（每行一个，`#` 开头的行是注释），运行时用 `--not-retrieved` 传给程序：程序跳过这些记录，在 `summary.json` 里列出；PRISMA 计数里记为 not retrieved，与按标准排除的分开。

**运行**

```sh
python screen_rules_template.py ta records.csv --output out/ta_v0.1
python screen_rules_template.py ft records.csv --after-ta out/ta_v0.1/decisions.csv --texts fulltext/ --output out/ft_v0.1
```

全文阶段只筛题目摘要阶段保留的记录，名单从 `--after-ta` 指定的结果文件里读。`--not-retrieved <清单文件>` 只用于全文阶段，见上面的输入。加 `--expect-sha256 <哈希>` 时，记录文件和冻结时不一致就拒绝运行。`--help` 显示全部选项。

**输出**（写到一个新目录，从不覆盖）

- `decisions.csv`：每条记录一行：决定（`keep` 或 `exclude`）、理由、不符合的标准、规则版本。
- `evidence.json`：每条标准命中的词和上下文，审计用。
- `summary.json`：输入文件的哈希、筛选的记录数、各决定的数量、取不到全文的记录清单。

**常见提示**

| 程序提示 | 意思 | 怎么办 |
|---|---|---|
| `records.csv needs the columns record_id, title and abstract` | 缺列 | 导出时带上这三列，列名要完全一致 |
| `record_id must be present and unique` | 有空的或重复的编号 | 回到去重那一步 |
| `the full-text phase needs --after-ta …` | 全文阶段没指定题目摘要阶段的结果 | 加 `--after-ta` |
| `retrieve the full text of every kept record first; missing: …` | 有保留记录还没有全文 | 先取来列出的记录的全文；确实取不到的写进清单，用 `--not-retrieved` 传入 |
| `--not-retrieved applies to the full-text phase only` | 题目摘要阶段用了这个参数 | 去掉；题目摘要阶段不用全文 |
| `the not-retrieved list names records that were not kept at the ta phase: …` | 清单里有不在题目摘要保留名单里的编号 | 核对编号；只有保留的记录才谈得上取全文 |
| `listed as not retrieved but the text file exists: …` | 清单和全文文件夹矛盾 | 有全文就从清单里去掉，没有就删掉那个文件 |
| `Output directory already exists; choose a new one` | 输出目录已存在 | 换一个新目录名，结果从不覆盖 |
| `records file does not match the expected hash` | 记录文件变了 | 确认是不是用错了文件；冻结的输入不能改 |

正式运行前，先在你已知应该纳入的论文上跑，它们必须全部保留。有漏的，改词表（改规则，不改单篇），升版本再跑。

## 4. 阶段计划 `plans/STAGE_PLAN.md`（模板 `plan_memo.md`）

每个调用 AI 的阶段写一份：筛选审计（S5）、编码（S8）、编码审计（S9）；如果由模型做筛选，S3、S4 也写。建项目时复制了一份 `plans/STAGE_PLAN.md`；一个阶段一份，文件名带上阶段，例如 `plans/S8_PLAN.md`。计划先写，然后才是 codebook、prompt、运行。

**标题行**

| 占位符 | 填什么 |
|---|---|
| `{{STAGE_NAME}}` | 阶段名。例：`Coding` |
| `{{VERSION}}` | 计划版本 |
| `{{OWNER}}` | 负责人，就是你 |

**第 1 节 研究问题与范围**

| 占位符 | 填什么 |
|---|---|
| `{{QUESTION}}` | 综述的研究问题 |
| `{{STAGE, e.g. coding audit, S9}}` | 阶段名和编号。例：`coding, S8` |
| `{{DECISIONS}}` | 这个阶段决定什么。例：`which conditions of each included paper become rows, and the value of every executor column` |
| `{{OUT_OF_SCOPE}}` | 这个阶段不能决定什么。例：`eligibility; effect sizes` |
| `{{FILE_AND_SHA256}}` | 纳入标准文件和哈希 |

**第 2 节 单位与输入**

| 占位符 | 填什么 |
|---|---|
| `{{ROW_UNIT}}` | 一行代表什么。例：`one study x condition x arm x outcome` |
| `{{IDENTITY_FIELDS}}` | 决定一行身份的字段，不含会变的数字。例：`Study_ID, Condition_ID, Arm, Outcome_Metric` |
| `{{SOURCES}}` | 允许用的来源和先后。例：`journal version, then preprint, then supplement; no external data` |
| `{{INPUT_MANIFEST}}` | 输入的版本、哈希、全文是否齐全。例：`papers/TRACKER.csv, sha256 …; 58 PDFs, all present` |
| `{{HANDLING}}` | 证据缺失、拿不到、互相矛盾时怎么办。例：`keep the row, leave the field null, record an unresolved item; never guess` |

**第 3 节 结果与计算**

| 占位符 | 填什么 |
|---|---|
| `{{OUTCOMES}}` | 结果指标的定义、方向、量纲。例：`cooperation rate = share of cooperative choices; higher = more cooperative` |
| `{{PAIRING}}` | 处理组和对照组怎么配对，共用样本怎么处理。例：`the LLM arm is paired with the human arm of the same game and treatment; a shared human baseline pairs with every LLM arm and is flagged` |
| `{{AGGREGATION}}` | 重复观测怎么合并。例：`repeated rounds of one agent are one observation, not independent units` |
| `{{EXTRACTED_FIELDS}}` | 执行模型提取的字段，即 executor 列 |
| `{{DERIVED_FIELDS}}` | 由程序计算的字段。例：`Row_UID, g, SE_g, CI95_L, CI95_U` |
| `{{ESTIMATOR}}` | 效应量的估计方法、假设、算不出的情形。例：`Hedges' g from means and SDs; undefined when either SD is missing` |

**第 4 节 角色与信息边界**

| 占位符 | 填什么 |
|---|---|
| `{{EXECUTOR}}` | 执行模型及其固定版本和设置。例：`provider X, model snapshot …, temperature 0` |
| `{{REVIEWERS}}` | 审计角色和各自能看什么，与 `validation/` 里的设计一致 |
| `{{HIDDEN_FIELDS}}` | 对模型隐藏的东西。例：`the executor's reasoning, other reviewers' answers, computed effects` |
| `{{HUMAN_BOUNDARY}}` | 什么情况交给人裁决，需要什么证据。例：`only when auditor and adjudicator disagree; the human cites the page` |

**第 5 节 试跑与验证**

| 占位符 | 填什么 |
|---|---|
| `{{PILOT}}` | 试跑用哪些论文，各自能检验什么。例：`5 papers: 2 clear cases, 1 with a missing SD, 1 with a shared baseline, 1 with many conditions` |
| `{{TARGET}}` | 验证针对哪种错误。例：`wrong effect-size inputs; wrong pairing` |
| `{{FRAME}}` | 全查还是抽样；分层、种子、顺序。例：`census of all included papers` |
| `{{STOPPING}}` | 停止规则和理由；什么情况升级处理 |
| `{{LIMITS}}` | 这次验证查不出什么。例：`errors shared by executor and auditor; eligibility errors` |

**第 6 节 运行与技术故障**

| 占位符 | 填什么 |
|---|---|
| `{{PREFLIGHT}}` | 运行前的离线检查。例：`check_codebook.py --ready passes; rendered prompts contain no placeholder; input hashes match` |
| `{{RETRY_POLICY}}` | 每项最多重试几次；断点续跑怎么做。例：`3 attempts per item, global attempt IDs, resume without resubmitting finished items` |
| `{{BUDGET_AND_APPROVAL}}` | 预算、允许的服务商、明确的运行批准。例：`USD 40 max; provider X; approved by … on 2026-09-20` |

**第 7 节 版本与完成**

| 占位符 | 填什么 |
|---|---|
| `{{CHANGE_POLICY}}` | 改动后哪些结果要重做、哪些可以沿用。例：`a codebook clarification reruns only the affected papers; the rest keep their version` |
| `{{DELIVERABLES}}` | 产出文件和路径 |
| `{{CHECKS}}` | 实际做过的独立检查 |
| `{{SCOPE}}` | 完成的范围 |
| `{{UNRESOLVED}}` | 未决定的事 |
| `{{APPROVAL}}` | 审核后的签字和日期。只在审核之后填 |

## 5. 筛选审计 `validation/screening/`（筛选审计，S5）

一套四类文件：`memo.md` 用文字写审计设计；`codebook.json` 是审计模型的规则；`config.json` 是运行设置；两个 prompt 是发给模型的话。memo 里决定的，codebook 和 config 里对应填；三份要互相一致。

### 5.1 `memo.md`

标题行：`{{VERSION}}` 审计版本；`{{SNAPSHOT_ID}}` 检索快照；`{{RULES_VERSION}}` 被审的筛选规则版本；`{{FILE_AND_SHA256}}` 纳入标准文件和哈希。

| 节 | 占位符 | 填什么 |
|---|---|---|
| 1 | `{{TARGET}}` | 审计找哪种错误。例：被筛选程序排除但本应保留的记录 |
| 2 | `{{ORDER_AND_REASON}}` | 两个审计的先后和理由。例：先审全文筛选，再审题目摘要筛选，因为题目摘要审计给出的"保留"要用冻结的全文筛选来处理 |
| 3 | `{{WHICH_RECORDS}}` | 全文审计审哪些记录。例：这个快照里全文阶段排除的全部记录 |
| 3 | `{{FRAME_FILE_AND_SHA256}}`、`{{N}}` | 这份清单的文件、哈希、条数 |
| 3 | `{{STRATA}}` | 分层。例：险些纳入（只有一条标准不符合）和其余 |
| 3 | `{{ROUND_SIZE_ALLOCATION_SEED}}` | 每轮抽多少、按层怎么分配、种子。例：每轮固定数量，按层分配，按种子生成的顺序抽，后续轮次接着抽 |
| 3 | `{{REVIEWERS_AND_ROUTING}}` | 审计者和流转。例：两位主审来自不同厂商；两者答案都有效但不一致时才请第三位；多数意见由程序计算 |
| 3 | `{{INPUTS}}`、`{{HIDDEN}}` | 每位审计者能看到什么、看不到什么。例：给记录编号、题目、完整 PDF、标准原文；不给程序的决定和理由、逐条标准的结果、层和序号、其他审计者的答案、下游结果 |
| 3 | `{{WHEN_AND_WITH_WHAT_EVIDENCE}}` | 什么时候由人裁决，要什么证据。例：只有审计多数认为应纳入时；人同意并给出页码才算确认漏排 |
| 4 | `{{WHICH_RECORDS}}`、`{{FRAME_FILE_AND_SHA256}}`、`{{N}}` | 题目摘要审计的总体，同上 |
| 4 | `{{STRATA_ROUND_SIZE_SEED}}` | 例：按检索批次分层，按比例分配，种子顺序 |
| 4 | `{{REVIEWERS}}`、`{{INPUTS}}`、`{{HIDDEN}}` | 例：每条记录一位审计者；给记录编号、题目、完整摘要或 null、标准原文；不给程序的决定、检索批次、任何 PDF、其他答案 |
| 4 | `{{CANDIDATE_ROUTE}}` | "保留"意味着什么、去哪里。例：保留是候选，不是错误；取全文，跑冻结的全文筛选，筛选纳入的交给第 3 节的全文审计者读 |
| 5 | `{{STOPPING_RULE}}` | 停止规则。例：一轮里没有候选通过冻结的全文筛选，审计结束；有候选通过但全被审计者排除的轮次计入累计；确认漏排之后审计继续；每累计若干个确认漏排就检查是否有系统性错误。没做完的事（缺 PDF、答案未定）不算零 |
| 6 | `{{RULE_CHANGE_POLICY}}` | 规则怎么改、确认的漏排改变什么。例：一轮审计期间规则不变，轮次结束后才改；任何记录都不靠手工加入纳入集；全文审计确认的漏排改全文规则（最小的一般性修订、升版本、全部重跑、归档当前审计、重新冻结样本）；题目摘要规则保持冻结，该审计确认的记录进入一份冻结清单，由全文筛选作为追加输入读取 |
| 7 | `{{RETRY_POLICY}}` | 例：拒答、格式错误、缺字段、身份不符，用同一请求重试，不算排除、投票或干净的一轮 |
| 7 | `{{WHAT_IS_REPORTED}}` | 例：每个阶段的总体大小、分层、轮数、种子、审了多少、候选数、确认漏排数、触发的停止条件、审计查不出什么 |

### 5.2 `codebook.json`

| 字段 | 填什么 |
|---|---|
| `version` | 审计 codebook 的版本 |
| `screening_rules_version` | 被审的筛选规则版本 |
| `canonical_eligibility.sha256` | 纳入标准的哈希；路径保持 `codebook/eligibility.json` |
| `target`、`order` | 同 memo 第 1、2 节。`order` 例：`full_text first, then abstract` |
| `modes.full_text.used_for` | 全文模式用在哪。例：全文排除的审计；题目摘要候选通过冻结全文筛选后的复核 |
| `modes.full_text.reviewers`、`human_adjudication` | 同 memo 第 3 节 |
| `modes.full_text.inputs`、`hidden`、`response`、`decision_values` | 已按常见设计填好；与 memo 不一致时改这里 |
| `modes.abstract.used_for`、`reviewers` | 题目摘要模式对应项 |
| `modes.abstract.retain_rule` | 什么时候保留。例：除非题目和摘要明确显示某条标准不符合，否则保留；保留是候选，不是错误 |
| `modes.abstract.candidate_route` | 同 memo 第 4 节 |
| `reason_codes` | 理由代码。`POTENTIALLY_ELIGIBLE` 保留不动；每条标准一个代码，把 `{{CODE_FOR_C1}}` 换成代码名，例如 `NOT_ECONOMIC_GAME`；有几条标准写几行，多余的行删掉 |
| `technical_failure` | 同 memo 第 7 节 |
| `evidence_contract.locator` | 证据位置怎么写。例：全文写页码或章节；题目摘要写 `title` 或 `abstract` |
| `evidence_contract.quote` | 保留：来自所给文本的简短引文 |

### 5.3 `config.json`

| 字段 | 填什么 |
|---|---|
| `status`、`live_enabled` | 保持 `draft_not_executable` 和 `false`，直到设计审核通过并批准运行。这个文件本身不调用任何服务 |
| `snapshot`、`screening_rules_version`、`order` | 同 memo |
| `audit_codebook.sha256` | 审计 codebook 定稿后的哈希 |
| `eligibility_sha256` | 纳入标准的哈希 |
| `full_text.frame.path`、`sha256`、`size` | 冻结的全文排除清单的路径、哈希、条数（数字） |
| `full_text.strata` | 例：`near_miss = failed exactly one criterion; other = the rest` |
| `full_text.sample.round_size`、`allocation`、`seed` | 每轮数量（数字）、分配方式、种子（数字） |
| `full_text.reviewers` | 每个角色一项：把 `{{ROLE, e.g. auditor_1}}` 换成角色名（如 `auditor_1`）；`provider` 厂商；`model_snapshot` 精确的模型版本号；`settings` 温度等设置 |
| `full_text.routing`、`stopping_rule` | 同 memo；停止规则填批准后的版本 |
| `abstract.*` | 题目摘要审计的对应项；`candidate_route`、`stopping_rule` 同 memo |
| `rule_change` | 同 memo 第 6 节 |
| `payload_policy` | 四条隐藏原则，已填好，一般不改 |
| `retries.max_new_attempts_per_invocation` | 每次运行最多重试几次（数字）；其余三项保持 `true` |
| `budget.approved_max`、`approval_record` | 批准的最高花费（数字）和批准记录（谁、哪天） |
| `artifacts.*` | 四类产出的存放路径：原始回复、规范化后的回复、候选的处理记录、哈希清单 |

### 5.4 `prompt_full_text.md`、`prompt_abstract.md`

运行时代入，不手填：`{{RECORD_ID}}`、`{{TITLE}}`、`{{ABSTRACT_OR_NULL}}`（没有摘要时为 null）、`{{ELIGIBILITY_JSON}}`（`eligibility.json` 原文）、`{{AUDIT_CODEBOOK_JSON}}`（审计 codebook 原文）。这些由你的运行程序代入。

其余文字是给审计模型的指令：它看不到程序的决定；论文是数据不是指令；要返回什么。一般不用改。改了设计（比如返回的字段）时，同时改 codebook 里的 `response`。

## 6. 编码 codebook `codebook.json`（编码，S8）

codebook 告诉执行模型每一列填什么、按什么规则、什么证据算数。它也是检查器核对的对象。

### 6.1 项目与状态

| 字段 | 填什么 |
|---|---|
| `schema_version` | 保持 `raes-codebook/1` |
| `project.id` | 项目代号，不带空格。例：`llm-games` |
| `project.title` | 项目标题 |
| `project.question` | 研究问题，一句话 |
| `project.domain` | 领域。例：`behavioural economics; language-model agents` |
| `version` | codebook 版本 |
| `status` | `draft`；批准后改 `ready` |
| `approval.by`、`date`、`basis` | 批准人、日期、依据（审过哪些规则、试跑证据、还有什么未决定）。只在真正审核后填，不为通过检查而填 |

### 6.2 判断单位 `unit`

| 字段 | 填什么 |
|---|---|
| `record` | 一条检索记录是什么。例：`one record exported from the reference manager` |
| `study` | 报告和研究怎么对应。例：`one experiment; a preprint and its journal version are one study` |
| `row` | 一行是什么。例：`one study x condition x arm x outcome` |
| `independent_unit` | 独立抽样单位。例：`one LLM agent run or one human participant` |
| `identity_fields` | 决定行身份的变量名。必须是 executor 填、不允许为空的字段；不含会变的数字 |

### 6.3 纳入标准 `eligibility`

`file` 保持 `eligibility.json`（与 codebook 同目录）；`sha256` 填按 0.2 节算出的哈希。

### 6.4 变量 `variables[]`

每个变量一个对象：

| 字段 | 填什么 |
|---|---|
| `name` | 变量名，字母开头，只用字母、数字、下划线；它就是表格的列名 |
| `type` | `string`、`number`、`integer`、`boolean`、`object` 或 `array` |
| `nullable` | 能否为空：`true` 或 `false` |
| `owner` | 谁填：`executor`（执行模型）或 `code`（程序）。`Row_UID`、`g`、`SE_g`、`CI95_L`、`CI95_U` 必须是 `code` |
| `description` | 一句话说明 |
| `rule` | 可核对的操作规则。例（N）：`Copy the number of independent agents in this arm, not the combined N of the study.` |
| `source_rule` | 允许的证据和位置。例：`The supplied paper only; cite an exact table or line for every non-null number.` |
| `missing_rule` | 缺失时怎么办：null、待定（unresolved）还是不适用（not applicable）。例：`If the path does not apply, null. If a required statistic is absent, null plus an unresolved item.` |
| `example` | 一个符合类型的例子；只有 `nullable` 为 `true` 时可以是 `null` |
| `counterexample` | 一个看似合理但错误的填法，以及为什么错。例（sd）：`An SE of 1.58 is not an SD of 10.0.` |
| `minimum`、`maximum`（可选） | 数值范围 |
| `allowed_values`（可选） | 允许的取值。例（Arm）：`["llm", "human"]` |

模板里的变量是一套示意：四个身份字段、效应量输入（`ES_Path`、`N`、`mean`、`sd`、`events`、`total`）、来源位置、三个程序字段。不适用的删掉，在 `plans/DECISIONS.md` 里写为什么；需要的变量（比如调节变量）按同样格式加。不要因为模板里有某个结果指标就保留它。

### 6.5 列表

| 字段 | 填什么 |
|---|---|
| `columns` | 全部变量名，顺序与 `variables` 完全一致，含 `code` 字段。检查器逐一核对 |
| `provenance_fields` | 记录证据位置的列，至少一个。例：`["Source_Location"]` |

`codebook/columns.csv` 和 `codebook/executor_columns.csv` 是建项目时从 codebook 生成的。变量改了以后要手动同步：各一行，逗号分隔；executor 那份去掉所有 `code` 字段。prompt 生成器直接读 codebook，不读这两个文件。

### 6.6 结果与规则

| 字段 | 填什么 |
|---|---|
| `outcome_map[]` | 论文里的指标怎么对应到统一名称。`source_measure` 论文里的写法，例：`share of cooperative choices`；`canonical_outcome` 统一名，例：`cooperation`；`direction` 数值高代表什么，例：`higher = more cooperative`；`scale_rule` 换算规则和分母，例：`proportion in [0, 1]; percentages divided by 100` |
| `pairing_rule` | 处理组和对照组怎么配对，缺对照怎么办。例：`Match Study_ID, Condition_ID and Outcome_Metric; exactly one llm arm and one human arm; no comparator from another study.` |
| `aggregation_rule` | 独立单位、重复观测、共用对照怎么处理。例：`Rounds of the same agent are not independent. A human baseline shared by several llm arms is used by each and flagged.` |
| `direction_rule` | 效应量的方向。例：`llm minus human; the sign convention is fixed before any result is seen.` |
| `source_precedence[]` | 来源优先级和冲突处理。例：`Journal version over preprint. A contradiction between text and table is unresolved, not overwritten.` |
| `unresolved_policy` | 待定项怎么记。例：`Keep the row, leave the field null, record the field, the reason and the affected row; never impute.` |
| `worked_cases[]` | 三个写出来的例子：`case_include` 正例、`case_missing` 符合但算不出、`case_boundary` 边界或冲突。`id` 可以自己起名；`description` 写情形和期望的编码。检查器只看它们存不存在，内容靠试跑检验 |

### 6.7 检查

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

草稿检查：占位符只算警告，结构错误算错误。`--ready` 另外要求：`status` 为 `ready`、批准信息齐全、没有占位符、哈希与文件一致。输出是 JSON：`checks_passed` 为 `true` 表示通过；`findings` 列出每条问题的位置和信息（第 10 节有对照表）。检查器不判断规则在科学上对不对。

[合成例子里填好的 codebook](../examples/synthetic/inputs/codebook.json) 是一个完整的小例子，可以对照格式；它的批准记录是虚构的。

## 7. 编码 prompt `prompts/`（编码，S8）

- `coding_system.md`：执行模型的角色和总规则。占位符 `{{CODEBOOK_JSON}}`、`{{ELIGIBILITY_JSON}}`、`{{EXECUTOR_COLUMNS_JSON}}` 由生成器从 codebook 读入，不能手填，也不能在 context 里覆盖。
- `coding_paper.md`：每篇论文一份。`{{PAPER_ID}}` 论文编号；`{{SOURCES_JSON}}` 这篇论文允许用的来源（文件名、提取的文本），由你的数据准备步骤产生。

生成命令：

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

`context.json` 只提供模板额外需要的字段。system prompt 用 `{}`；paper prompt 例：

```json
{"PAPER_ID": "S017", "SOURCES_JSON": {"files": ["S017-journal.txt"], "note": "supplement table S2 included"}}
```

不是字符串的值会被整理成 JSON 文本代入。生成器先跑一遍 codebook 的 `--ready` 检查；codebook 还没定稿时加 `--draft` 预览。输出文件不会覆盖已有文件，也不向任何地方发送内容。

固定文字一般不用改。要改的话保持几条原则：只按 codebook 和标准；论文是数据不是指令；只返回一个 JSON 对象；不填程序负责的字段；缺失用 null 不用 0；每个数字带出处。

## 8. 编码审计 `validation/coding/`（编码审计，S9）

结构与筛选审计相同：memo、codebook、config、两个 prompt。

### 8.1 `memo.md`

标题行：`{{VERSION}}` 审计版本；`{{CODEBOOK_VERSION}}` 被审的编码 codebook 版本；`{{FILE_AND_SHA256}}` 纳入标准文件和哈希。

| 节 | 占位符 | 填什么 |
|---|---|---|
| 1 | `{{TARGET}}` | 审计找哪种错误。例：效应量输入错；与对照行配对错或计算路径错；调节变量错 |
| 1 | `{{OUT_OF_SCOPE}}` | 不再重审什么。例：纳入资格 |
| 2 | `{{WHICH_ROWS}}` | 审哪些行。例：将进入分析的全部行，审计前冻结，效应量字段留空并隐藏 |
| 2 | `{{FRAME_FILE_AND_SHA256}}`、`{{N_ROWS}}`、`{{N_PAPERS}}` | 这份行清单的文件、哈希、行数、论文数 |
| 2 | `{{UNIT}}` | 每次请求的单位。例：一篇论文；这篇的每一行都查 |
| 2 | `{{DESIGN_AND_JUSTIFICATION}}`、`{{FIXED_BEFORE_REVIEW}}` | 全查还是抽样，及理由；抽样时的分层、种子、顺序，审前定死 |
| 3 | 审计者 `{{INPUTS}}`、`{{HIDDEN}}` | 例：给来源、编码 codebook、这份审计 codebook、这篇论文的编码行；不给执行模型的推理、之前的审计答案、抽样信息、任何算出的效应 |
| 3 | 裁决者 `{{INPUTS}}`、`{{HIDDEN}}` | 例：给同样的来源和规则、原始行、被质疑的字段及其当前值；不给审计者提出的值、证据、理由、置信度。看到被审的当前值不影响独立性，看到建议值才会 |
| 4 | `{{DOMAINS}}` | 查什么。例：1. 效应量输入及出处；2. 每行与对照行的配对和计算路径；3. 需要判断的调节变量 |
| 5 | `{{ROUTING}}` | 流转。例：审计者返回通过，或一条质疑（行、字段、建议值、规则、证据），或待定项；每条质疑交裁决者，裁决者返回三种结果之一：现有编码成立（驳回质疑，不需要人）；改正成立（与审计者的隐藏建议完全一致才确认，有差异交人裁决）；来源或规则有歧义（交人裁决） |
| 5 | `{{PROHIBITED}}` | 审计者不能做什么。例：增、删、拆、并行；重审纳入资格 |
| 6 | `{{CORRECTION_POLICY}}` | 例：审计从不改原始行；属于单篇、规则本来清楚的错误，写进单独的调和记录（保留改前改后的值），由程序生成新版本的表；暴露出规则不清或有错的错误，改 codebook、升版本、受影响的论文重新编码；重跑编码模型只用于技术故障；作者更正的数值和已发表的勘误也通过这份调和记录进入，注明来源；codebook 澄清后只重审受影响的论文，之前的通过结果保留当时的 codebook 版本 |
| 7 | `{{RETRY_POLICY}}` | 例：拒答、格式错误、缺字段、身份不符，用同一请求重试，不算通过 |
| 7 | `{{WHAT_IS_REPORTED}}` | 例：总体的行数和论文数、查了多少、质疑数、确认改正数、待定项、人裁决数、审计不覆盖什么 |

### 8.2 `codebook.json`

| 字段 | 填什么 |
|---|---|
| `version` | 审计 codebook 的版本 |
| `production_codebook_version` | 被审的编码 codebook 版本 |
| `canonical_eligibility.sha256` | 纳入标准的哈希 |
| `scope.frame` | 总体的编号。例：`frame-2026-09-17-v1` |
| `scope.units` | 审哪些行。例：`all Row_UIDs in the frame` |
| `scope.allowed_domains`、`prohibited_actions` | 同 memo 第 4、5 节 |
| `modes.coding_audit.*`、`modes.coding_adjudication.*` | 两个角色各自的输入、隐藏项、返回字段。已按常见设计填好；与 memo 不一致时改这里。裁决者的 `outcomes` 是三种结果：现有编码成立、改正成立、来源或规则有歧义 |
| `pass_rule` | 什么算通过。例：`Every checked Row_UID is covered in every allowed domain and no unresolved evidence remains.` |
| `challenge_rule` | 一条质疑要包含什么。例：行和字段、有来源支持的替代值、规则编号、能找到的位置 |
| `conflict_rule` | 来源冲突怎么办。例：按 `source_precedence`；否则人裁决；从不编造值 |
| `error_taxonomy` | 错误分类，一般保留 |
| `evidence_contract.source_id`、`locator`、`quote_or_data_reference` | 证据怎么写：来源文件名或稳定编号；页、表、行、格；引文或数据引用 |

### 8.3 `config.json`

| 字段 | 填什么 |
|---|---|
| `status`、`live_enabled` | 同筛选审计，保持不变直到批准 |
| `frame.path`、`sha256`、`unit` | 冻结的行文件、哈希、单位 |
| `rules.production_codebook` | 编码 codebook 的路径。例：`codebook/codebook.json` |
| `rules.eligibility_sha256` | 纳入标准的哈希 |
| `reviewers.executor`、`auditor`、`adjudicator` | 三个角色的厂商、精确模型版本、设置。审计者尽量用与执行模型不同的厂商 |
| `sampling.mode` | `census`（全查）或说明抽样设计；抽样时填 `strata`、`seed`、`round_size` |
| `routing` | 同 memo 第 5 节 |
| `payload_policy` | 已填好，一般不改 |
| `retries`、`budget`、`artifacts` | 同筛选审计；`artifacts.reconciliation` 是调和记录的路径 |

### 8.4 `prompt_audit.md`、`prompt_adjudicator.md`

运行时代入，不手填：`{{ELIGIBILITY_JSON}}`、`{{CODEBOOK_JSON}}`、`{{AUDIT_CODEBOOK_JSON}}`、`{{SOURCES_JSON}}`、`{{TARGET_ROWS_JSON}}`（原始的目标行，效应量字段留空）、`{{COORDINATE_JSON}}`（裁决者要判断的行、字段和当前值）。

裁决者的 prompt 里有当前值，没有审计者的建议值和证据，这是设计的一部分，不要加进去。它返回三种结果之一：现有编码成立、改正成立（附改正值）、来源或规则有歧义。

## 9. 项目起始文件 `project/`

- `README.md`：项目文件夹的说明。开头补上项目名和一句话的研究问题；其余说明可以保留。
- `CURRENT_STATUS.md`：项目状态。`Status` 一行在批准运行前保持 `DRAFT — no collection authorized`（草稿，未批准收集）；`Completed scope` 每完成一个阶段更新，只写已经完成的，不写推测的下一步。
- `.gitignore`：不进版本库的东西：密钥（`.env`、`*.key`、`secrets/`）、软件环境、缓存、`_internal/`，以及默认不公开的研究材料：`search/raw/`、`papers/`、`validation/raw/`。分享前检查一遍；已经跟踪的文件不会因为加了规则而消失。
- `plans/DECISIONS.md`（程序生成）：所有操作选择的记录。每个提议先写在这里，标明是提议还是已批准。

## 10. 检查器提示对照

`check_codebook.py` 的 `findings` 里常见的信息：

| 信息 | 意思 | 怎么办 |
|---|---|---|
| `unresolved placeholder` | 某处还有 `{{`、`TODO` 等 | 做决定填上。草稿阶段是警告，`--ready` 时是错误 |
| `required section missing` | 缺顶层字段 | 不要删模板的顶层字段 |
| `nonempty text required` | 必填文字为空 | 填上 |
| `columns must match ordered variable names exactly, including code-owned columns` | `columns` 与 `variables` 不一致 | 按 `variables` 的顺序重写 `columns` |
| `identity fields must be non-null, executor-owned source IDs` | 身份字段允许为空，或由程序填 | 身份字段设 `nullable: false`、`owner: executor` |
| `this identifier/statistic is reserved for deterministic code` | `Row_UID`、`g`、`SE_g`、`CI95_L`、`CI95_U` 的 `owner` 不是 `code` | 改为 `code` |
| `example key required …`、`expected integer, got float`、`violates minimum` | 例子与类型或范围不符 | 改例子或改类型、范围 |
| `canonical eligibility bytes differ` | 记录的哈希与文件不符 | 重新算哈希。如果标准改了，升版本并记录影响 |
| `file not found`（`eligibility.file`） | 纳入标准文件不在 codebook 同目录 | 放到 `codebook/` 下，路径写 `eligibility.json` |
| `ready check requires explicit ready status` | 用了 `--ready` 但 `status` 不是 `ready` | 审核通过后再改 `ready` |
| `ISO YYYY-MM-DD required` | 日期格式不对 | 改成 `2026-09-17` 这样的格式 |
| `Duplicate JSON key` | 同一层有重复的键 | 删掉重复的 |

## 11. 一个阶段的完整顺序

1. 计划：写阶段计划（第 4 节）。
2. 规则：写 codebook、审计 codebook 或筛选规则，草稿检查通过。
3. 审核、批准，算哈希，跑 `--ready` 检查。
4. prompt：生成或核对。
5. 试跑三到五篇；有问题改规则（改一般规则，不改单篇），升版本。
6. 冻结（`tools/freeze.py` 写哈希清单），然后运行。运行程序是你自己的；RAES 不向任何服务商发请求。
7. 更新 `CURRENT_STATUS.md` 和 `plans/DECISIONS.md`。
8. 阶段完成后做一次发布：`python tools/release.py --project <项目> create <名字>`，再 `activate <名字>`。它原地记录每个文件的哈希，不复制文件；之后 `verify` 能查出任何改动。重建全部结果时，用 `python tools/run_offline.py -- <命令>` 在断网状态下跑。
