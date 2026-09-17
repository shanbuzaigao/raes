# Codebook-author Skill

[English](README.md) | [简体中文](README.zh-CN.md)

这一版只做一个 [codebook-author](codebook-author/SKILL.md)。采用标准 Agent Skills 目录：`SKILL.md` 加脚本、问题指南、骨架。安装时复制整个目录；检查器不依赖 RAES 仓库的其他代码。

在 RAES 根目录运行：

```sh
python tools/install_skill.py --destination ~/.claude/skills
```

这是 Claude Code 的个人 Skill 目录；项目安装可以改为目标项目的 `.claude/skills`。工具自行展开 `~`，发现已有同名 Skill 就停止，不覆盖。重新加载宿主后，在 Claude Code 中用 `/codebook-author` 调用。例如：“帮我为 structured versus plain feedback 的综述写 codebook，先问清研究问题、单位和纳入标准，不要发 API 请求。”

Skill 会先读已有规则，分小批提问，形成计划、统一纳入标准、codebook、列模板、prompt 草稿和未解决事项，再运行本地检查并准备一个小试例。没有执行工具的宿主只能提供命令，并须说明没有实际运行检查。

安装路径依据 [Claude Code 官方说明](https://code.claude.com/docs/en/skills)，目录依据 [Agent Skills 规范](https://agentskills.io/specification)。不同宿主的装载方式可能不同；这里没有宣称已经逐一测试。

[合成题目演练](../examples/codebook_author_rehearsal.md) 是脚本化的本地演练，不是伪造的 Claude 对话或用户测试。已检查复制后脚本可运行；仍应在你真正使用的宿主里试一次交互，再决定是否做 validation-designer。验证设计的模板已提供，但第二个 Skill 没有提前做。
