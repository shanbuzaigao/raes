# 写作模板

[English](README.md) | [简体中文](README.zh-CN.md)

这一层回答“怎么写”，不是已经替你确定了研究设计。先写问题、判断单位和批准的纳入标准，再决定需要哪些字段。`{{...}}` 都要填写；骨架能通过草稿结构检查，但应当无法通过 `--ready`。模板不会授权采集、付费调用或发布。

## 创建一个草稿项目

在 RAES 根目录运行，目标须是仓库之外的新目录：

```sh
python tools/new_project.py ../my-evidence-project
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json
```

生成的目录已有计划 memo、codebook 和 eligibility、两份列名 CSV、prompt、验证配置，以及每个工作目录的职责说明。已有目标目录不会被覆盖。

填完并得到研究者实际批准后，记录批准信息，把 `status` 设为 `ready`，填入 `eligibility.json` 文件实际字节的 SHA-256，再运行：

```sh
python tools/check_codebook.py ../my-evidence-project/codebook/codebook.json --ready
```

Windows 可以把 `python` 换成已配置的 Python 启动器。全套本地工具不需要第三方依赖。

## 按什么顺序填？

先填 [计划 memo](plan_memo.md)：问题、单位、输入输出、盲法边界、pilot、完成标准和授权。再填 [eligibility](eligibility.json) 与 [codebook](codebook.json)：规则、字段类型、允许值、缺失处理、来源、反例、配对和聚合。然后准备 [验证计划](validation_memo.md)、[共享审计 codebook](validation_codebook.json) 和 [验证配置](validation_config.json)。最后才从这些规则写 prompt。

骨架以 arm-level 效应量输入为例，不要求每个项目照搬。删除不适用字段时写明原因，不因为模板里有一个字段就增设研究 outcome。`columns` 必须按顺序列出所有变量；executor 列表另行排除 `owner=code` 的字段。`Row_UID`、`g`、`SE_g` 和置信区间只由程序填写。

AI2 和 AI3 使用同一份审计 codebook，但任务模式和输出不同。AI2 需要看到原始目标值；AI3 可看到同样的原始目标和待核查坐标，但不能看到 AI2 建议的值或理由。

## 怎样保持纳入标准一致？

把批准文字保存在一个 canonical eligibility 文件中，不在各阶段另写近义版本。更新后计算字节哈希：

```sh
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('../my-evidence-project/codebook/eligibility.json').read_bytes()).hexdigest())"
```

填入 codebook 的 `eligibility.sha256`。换行符也属于字节；已冻结规则发生变化，需要版本与影响范围说明，而不是直接换哈希以通过检查。

## 本地生成 prompt

`tools/render_prompt.py` 自动装入完整 codebook、eligibility 原文和 executor 列名。其余内容由显式 context JSON 提供；system prompt 不需要额外内容时，context 就是 `{}`。

```sh
python tools/render_prompt.py --codebook ../my-evidence-project/codebook/codebook.json --template templates/prompts/coding_system.md --context ../my-evidence-project/context.json --output ../my-evidence-project/coding_system_rendered.md
```

`--draft` 仅用于未完成草稿预览；默认要求 ready 检查通过。输出已有则停止，不发任何 API 请求。编码 paper prompt 与不同审计角色的 prompt 分别生成。

## 检查器能说明什么？

它检查 `raes-codebook/1` 的必要章节、字段/列名一致性、类型/范围/例子、标识字段、程序计算字段归属、criterion ID，以及 eligibility 的哈希。它不是任意 JSON Schema 验证器，不判断研究设计正确、文献是否漏检、证据是否真的支持结论或样本量是否充分。`worked_cases` 的科学含义仍需研究者审阅和小范围试用。

[已填写的合成 codebook](../examples/synthetic/inputs/codebook.json) 可以作为实例，但其中的批准记录明确是虚构的，不能复制成真实批准。
