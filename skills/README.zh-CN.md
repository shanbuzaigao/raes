# raes skill

[English](README.md) | [简体中文](README.zh-CN.md)

本文件夹包含一个覆盖整个工作流的 skill：[raes](raes/SKILL.md)。装进支持 Agent Skills 的宿主之后，它会引导研究者按照操作手册逐阶段推进：询问当前阶段所需的决定，用模板写文件，运行本地检查，并把每个调用 AI 的步骤按“计划、codebook、prompt、运行”的顺序准备好。它不调用模型 API，也不真正运行筛选或编码。

这个文件夹遵循 [Agent Skills 规范](https://agentskills.io/specification)：

| 路径 | 内容 |
|---|---|
| `raes/SKILL.md` | 说明：怎么开始、每个阶段都适用的规则、阶段索引、检查项 |
| `raes/references/` | 每个阶段一份文件：问什么、写什么、进入下一阶段前检查什么 |
| `raes/assets/` | 仓库 `templates/` 文件夹的副本，这样 skill 装好之后可以独立工作 |
| `raes/scripts/new_project.py` | 用模板新建一个草稿状态的项目文件夹 |
| `raes/scripts/check_templates.py` | skill 更新之后用：显示已有项目里哪些模板过期了，并且只替换还没填过的副本 |
| `raes/assets/search/dedupe_records.py` | 复制进每个新项目。不用文献管理软件时做 S2：对 PubMed、Web of Science 或 RIS 格式的导出文件去重，写出记录表、台账、拿不准的记录对和各项数量 |
| `raes/scripts/check_codebook.py` | 检查 codebook，草稿模式或 `--ready` 模式 |
| `raes/scripts/check_dispersion.py` | 编码审计进入裁决之前，标出那些看起来像标准误的标准差 |
| `raes/scripts/release.py` | 为一次项目发布生成文件哈希清单（文件保留在原位置），指定当前生效的发布包，并据此核验工作副本 |
| `raes/scripts/run_offline.py` | 运行一条命令（比如重建全部结果的命令），它启动的 Python 进程都不能联网 |

## 安装

Claude Code 的个人 skill 放在 `~/.claude/skills/<name>/`，项目 skill 放在 `<project>/.claude/skills/<name>/`。在这个仓库下运行：

```sh
python tools/install_skill.py --destination ~/.claude/skills
```

安装程序复制整个文件夹；如果目标位置已经存在 `raes`，安装程序会拒绝覆盖。skill 更新后，如需更新已安装的版本，加 `--replace`：安装程序先确认已有的文件夹确实是一份 raes skill，再删掉它，复制当前版本。

```sh
python tools/install_skill.py --destination ~/.claude/skills --replace
```

重启或重新加载宿主，然后输入 `/raes`，说明你在哪个阶段，例如：

> /raes 我有一个关于结构化反馈和普通反馈的研究问题，还没有任何文件。从 S0 开始。

同一个文件夹在其他支持这种格式的宿主里也能用。Codex 从 `~/.agents/skills` 读个人 skill，从 `<repo>/.agents/skills` 读仓库 skill，调用时写 `$raes`：

```sh
python tools/install_skill.py --destination ~/.agents/skills
```

Gemini CLI、Cursor、GitHub Copilot 等各自的路径见 [Agent Skills 的客户端列表](https://agentskills.io/clients)。宿主不能运行 Python 时，skill 会给出确切的命令，并说明这项检查没有运行。

## 状态

skill 已在本地检查过：复制出去的文件夹独立可用，脚本能运行。它在 Claude Code 里试用过三次。第一次仅测试了 S0 的起始部分。第二次在另一个学科的项目（老年人的运动与抑郁症状）中完整走完了 S0 到 S12 的全部阶段，包括真实检索、筛选审计、编码、编码审计、分析和发布；此次试用中发现的问题促成了 0.4.0 版的修改。第三次在一个小题目上试了 0.4.0 的新工具，发现的问题促成了 0.4.1 版的修改。三次试用里，skill 都是询问需要的决定，明确区分建议与决定，并将最终决定留给研究者。[一份脚本化的演练](../examples/raes_rehearsal.md)用一个虚构的小题目走了一遍 codebook 阶段，可以看到提问和产出是什么样子。
