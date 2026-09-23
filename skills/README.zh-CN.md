# raes skill

[English](README.md) | [简体中文](README.zh-CN.md)

一个 skill，[raes](raes/SKILL.md)，覆盖整个流程。装进支持 Agent Skills 的宿主之后，它带着研究者按操作手册的阶段走：问出这一阶段需要的决定，用模板写文件，跑本地检查，并把每个调用 AI 的环节按“计划、codebook、prompt、运行”的顺序准备好。它不调用模型 API，也不做真实的筛选或编码。

文件夹遵循 [Agent Skills 规范](https://agentskills.io/specification)：

| 路径 | 内容 |
|---|---|
| `raes/SKILL.md` | 说明书：怎么开始、每个阶段都适用的规则、阶段索引、检查 |
| `raes/references/` | 每个阶段一个文件：问什么、写什么、进入下一步前检查什么 |
| `raes/assets/` | 仓库 `templates/` 文件夹的副本，装到别处后 skill 也能独立工作 |
| `raes/scripts/new_project.py` | 用模板建一个草稿项目文件夹 |
| `raes/scripts/check_templates.py` | skill 更新之后：显示已有项目里哪些模板过期了，并且只替换还没填过的副本 |
| `raes/assets/search/dedupe_records.py` | 建项目时复制进项目。不用文献管理软件时做 S2：对 PubMed、Web of Science、RIS 三种格式的导出文件去重，写出记录表、台账、拿不准的配对和各项数量 |
| `raes/scripts/check_codebook.py` | 检查 codebook，草稿模式或 `--ready` 模式 |
| `raes/scripts/check_dispersion.py` | 编码审计进入裁决之前，标出看起来其实是标准误的标准差 |
| `raes/scripts/release.py` | 给项目做发布：原地记录每个文件的哈希，不复制文件；指定当前生效的发布；核对工作副本与发布是否一致 |
| `raes/scripts/run_offline.py` | 在切断网络的情况下运行一条命令（比如重建全部结果的命令），对它启动的 Python 子进程生效，不是防火墙 |

## 安装

Claude Code 的个人 skill 放在 `~/.claude/skills/<名字>/`，项目 skill 放在 `<项目>/.claude/skills/<名字>/`。在本仓库下运行：

```sh
python tools/install_skill.py --destination ~/.claude/skills
```

安装程序复制整个文件夹，发现已有同名的 `raes` 就停止，不覆盖。skill 改过之后要更新已装的那份，加 `--replace`：安装程序先确认已有的文件夹确实是一份 raes skill，再删掉它、复制当前版本。

```sh
python tools/install_skill.py --destination ~/.claude/skills --replace
```

重启或重新加载宿主后，输入 `/raes`，说明你在哪一步，例如：

> /raes 我有一个关于结构化反馈和普通反馈的研究问题，还没有任何文件。从 S0 开始。

同一个文件夹在其他支持这种格式的宿主里也能用。Codex 从 `~/.agents/skills` 读个人 skill，从 `<仓库>/.agents/skills` 读仓库 skill，调用时写 `$raes`：

```sh
python tools/install_skill.py --destination ~/.agents/skills
```

Gemini CLI、Cursor、GitHub Copilot 等各自的路径见 [Agent Skills 的客户端列表](https://agentskills.io/clients)。宿主不能运行 Python 时，skill 会给出确切的命令，并说明检查没有运行。

## 状态

skill 已在本地检查过：复制出去的文件夹独立可用，脚本能运行。它在 Claude Code 里试用过三次。第一次只走了 S0 的开头。第二次在另一个学科的题目（运动干预与老年人抑郁症状）上走完了 S0 到 S12 的全部阶段，包括真实检索、筛选审计、编码、编码审计、分析和发布；这次发现的问题成了 0.4.0 版。第三次在一个小题目上试了 0.4.0 的新工具，发现的问题成了 0.4.1 版。三次试用里，skill 都是问出需要的决定、把建议明确标为建议、把决定留给研究者。[一份脚本化的演练](../examples/raes_rehearsal.md)用一个编造的小题目走了一遍 codebook 阶段，可以看到提问和产出是什么样子。
