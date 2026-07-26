# 全局 AGENTS.md 路由安装

## 为什么需要这一层

Codex 可以根据 Skill 的 `description` 隐式调用。全局 `AGENTS.md` 路由进一步固定分类标准：用户交付的是需要持续承担判断和推进责任的事情时，加载 `$chief-of-staff-collaboration`；用户只索取边界清楚的单次产物时，按普通任务处理。

Skill 本体负责触发后的判断与行动，全局 `AGENTS.md` 只负责何时加载。两层不能互相复制。

## 推荐安装方式

安装 Skill 后执行：

```powershell
& "$HOME\.codex\skills\chief-of-staff-collaboration\scripts\install-global-agents-route.ps1"
```

预览而不写入：

```powershell
& "$HOME\.codex\skills\chief-of-staff-collaboration\scripts\install-global-agents-route.ps1" -WhatIf
```

脚本默认修改 `$HOME\.codex\AGENTS.md`，并具有以下行为：

- 文件不存在时创建；
- 文件存在时先生成带时间戳的备份；
- 通过开始和结束标记识别自己的区块；
- 重复执行时更新原区块，不重复追加；
- 如果发现同名但没有标记的手工区块，则停止并要求人工核对，避免误删其他说明。

如需写入其他位置，可传入：

```powershell
.\scripts\install-global-agents-route.ps1 -AgentsPath "D:\path\to\AGENTS.md"
```

## 手工安装区块

不使用脚本时，将以下完整区块加入全局 `AGENTS.md`：

```markdown
<!-- BEGIN chief-of-staff-collaboration route -->
## 参谋型协作 Skill 路由

**总纲**：当用户交付的是一项需要 Codex 持续承担判断与推进责任的事情，而不只是索取一个边界清楚的单次产物时，自动使用 `$chief-of-staff-collaboration`。以用户真实目标为方向，以现实为校正，以授权为行动边界，以可验证结果为结束。

### 自动触发

- 用户明确要求以参谋、幕僚、秘书、chief of staff 的方式协作，或说“你来判断”“你看着办”“帮我想清楚并做完”“持续跟进”。
- 用户给出的目标仍不完整、相互冲突或会继续变化，同时希望 Codex 帮助确定优先级、作出建议并继续推进。
- 一项工作跨越判断、决定、执行和反馈多个阶段，需要保持上下文、处理例外或在关键节点请求授权。
- 需要处理重要的向上沟通、同级协调、下属反馈、关系修复或其他兼顾事实与接受方式的敏感互动。
- 对话开始时只是普通任务，但随后出现上述委托责任、重大取舍、持续推进或敏感协调信号，应从该轮起自动加载。

### 不触发

- 简单问答、事实解释、翻译、单句改写、机械格式调整和闲聊。
- 目标、范围和验收已经清楚的普通单次实现；正常完成和验证即可。
- 用户只要一个明确产物，并未委托 Codex 持续承担优先级判断、协调或异常处置。

### 加载边界

- 触发后读取完整 `SKILL.md`，只按当下问题加载宪法边界或互动手法参考，不把整个参考库塞入每次任务。
- Skill 只改变协作深度，不扩大用户授权，也不要求把简单任务包装成参谋工作。
<!-- END chief-of-staff-collaboration route -->
```

完成安装后开启一个新任务验证触发。若 Skill 刚安装但没有出现在 Codex 中，重启 Codex。
