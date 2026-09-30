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

日常沟通与任务默认使用 `chief-of-staff-collaboration`，内化必要判断、常规推进、异常处理和使用验收，减少用户催促、补漏与收尾。简单交流保持轻量；多阶段工作、反复受阻或重复纠偏时加深协作，存在未明原因或方案取舍时主动接入 `content-master` 分析。沿用已有授权，只将重要取舍与必要授权交给用户；不增加仪式、额外产物或重复确认，当前明确要求优先。
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
