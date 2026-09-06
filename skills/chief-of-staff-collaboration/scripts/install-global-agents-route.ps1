[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$AgentsPath = (Join-Path $HOME ".codex\AGENTS.md")
)

$ErrorActionPreference = "Stop"

$beginMarker = "<!-- BEGIN chief-of-staff-collaboration route -->"
$endMarker = "<!-- END chief-of-staff-collaboration route -->"
$routeHeading = "## 参谋型协作 Skill 路由"

$routeBlock = @'
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
- 一次性采购、硬件配置、产品或技术选型，即使用户说“你直接帮我选”，只要目标与后果边界清楚，也按普通决策支持处理。

### 加载边界

- 触发后读取完整 `SKILL.md`，只按当下问题加载宪法边界、互动手法或偏好约束参考，不把整个参考库塞入每次任务。
- Skill 只改变协作深度，不扩大用户授权，也不要求把简单任务包装成参谋工作。
<!-- END chief-of-staff-collaboration route -->
'@

$resolvedAgentsPath = [System.IO.Path]::GetFullPath($AgentsPath)
$agentsDirectory = Split-Path -Parent $resolvedAgentsPath
$current = if (Test-Path -LiteralPath $resolvedAgentsPath) {
  [System.IO.File]::ReadAllText($resolvedAgentsPath)
} else {
  ""
}

$hasBegin = $current.Contains($beginMarker)
$hasEnd = $current.Contains($endMarker)

if ($hasBegin -xor $hasEnd) {
  throw "Found only one chief-of-staff route marker in $resolvedAgentsPath. Repair the marker pair before retrying."
}

if (-not $hasBegin -and $current.Contains($routeHeading)) {
  throw "Found an unmarked '$routeHeading' section in $resolvedAgentsPath. Reconcile it manually before running this installer."
}

if ($hasBegin) {
  $pattern = "(?s)" + [regex]::Escape($beginMarker) + ".*?" + [regex]::Escape($endMarker)
  $updated = [regex]::Replace($current, $pattern, $routeBlock, 1)
} elseif ([string]::IsNullOrWhiteSpace($current)) {
  $updated = $routeBlock + [Environment]::NewLine
} else {
  $updated = $current.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + $routeBlock + [Environment]::NewLine
}

if ($updated -eq $current) {
  Write-Host "Global route is already up to date: $resolvedAgentsPath"
  return
}

if ($PSCmdlet.ShouldProcess($resolvedAgentsPath, "Install chief-of-staff collaboration route")) {
  if (-not (Test-Path -LiteralPath $agentsDirectory)) {
    New-Item -ItemType Directory -Path $agentsDirectory -Force | Out-Null
  }

  if (Test-Path -LiteralPath $resolvedAgentsPath) {
    $backupPath = "$resolvedAgentsPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item -LiteralPath $resolvedAgentsPath -Destination $backupPath
    Write-Host "Backup created: $backupPath"
  }

  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($resolvedAgentsPath, $updated, $utf8NoBom)
  Write-Host "Installed chief-of-staff collaboration route: $resolvedAgentsPath"
}
