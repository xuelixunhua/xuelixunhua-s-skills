# 全局路由安装

日常沟通默认加载参谋技能；深度随任务变化。全局只维护下面的短路由，具体协作判断在 SKILL.md，专项细则按需读取。

安装或更新可运行 [安装脚本](../scripts/install-global-agents-route.ps1)；`-WhatIf` 仅预览，`-AgentsPath` 可指定目标。默认目标为当前用户 `.codex/AGENTS.md`。已有内容会先备份，带标记区块就地更新；发现不完整标记或同名未标记区块时停止，核对后再处理。

```markdown
<!-- BEGIN chief-of-staff-collaboration route -->
## 参谋型协作 Skill 路由

日常沟通与任务默认使用 `chief-of-staff-collaboration`，内化必要判断、常规推进、异常处理和使用验收，减少用户催促、补漏与收尾。简单交流保持轻量；多阶段工作、反复受阻或重复纠偏时加深协作，存在未明原因或方案取舍时主动接入 `content-master` 分析。沿用已有授权，只将重要取舍与必要授权交给用户；不增加仪式、额外产物或重复确认，当前明确要求优先。
<!-- END chief-of-staff-collaboration route -->
```

安装后在新任务验证加载；当前对话已有的旧指令文本不会被磁盘改写替换。
