[CmdletBinding(SupportsShouldProcess)]
param(
  [string[]]$Skills,
  [string]$SourceRoot = (Join-Path $HOME ".codex\skills")
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$skillsRoot = [IO.Path]::GetFullPath((Join-Path $repoRoot "skills"))
$sourceBase = (Resolve-Path -LiteralPath $SourceRoot).Path
$manifest = Get-Content -LiteralPath (Join-Path $repoRoot "manifest.json") -Raw | ConvertFrom-Json
$entries = @($manifest.skills)

if ($Skills) {
  foreach ($name in $Skills) {
    if ($name -notin $entries.name) { throw "Unknown skill: $name" }
  }
  $entries = @($entries | Where-Object { $_.name -in $Skills })
}

# Exclude local state before copying anything into the public working tree.
function Test-PublicFile([string]$RelativePath) {
  $path = $RelativePath.Replace('\', '/')
  if ($path -match '(^|/)(\.git|\.claude|\.codex|\.learnings|__pycache__|node_modules|work|tmp)(/|$)') { return $false }
  if ($path -match '(^|/)(config\.env|\.env(?:\..*)?|auth\.json|credentials\.json|\.DS_Store|Thumbs\.db)$') { return $false }
  if ($path -match '\.(log|tmp|py[co])$' -or $path -match '^evals/results/') { return $false }
  if ($path -match '^evals/completed-work-regressions-.*\.json$') { return $false }
  if ($path -eq 'references/site-patterns/tingwu.aliyun.com.md') { return $false }
  return $true
}

# Check all exact targets before replacement; links could escape these paths.
foreach ($root in @($repoRoot, $skillsRoot, $sourceBase)) {
  if ((Test-Path -LiteralPath $root) -and ((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw "Linked root is not supported: $root"
  }
}
$plan = foreach ($entry in $entries) {
  $name = $entry.name
  if ($name -notmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$' -or $entry.path -cne "skills/$name" -or $entry.source -cne "~/.codex/skills/$name") {
    throw "Invalid maintainer mapping for skill: $name"
  }
  $source = [IO.Path]::GetFullPath((Join-Path $sourceBase $name))
  $dest = [IO.Path]::GetFullPath((Join-Path $skillsRoot $name))
  if ((Split-Path -Parent $dest) -ne $skillsRoot -or $source -eq $dest -or
      $source.StartsWith($dest + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
      $dest.StartsWith($source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe sync destination: $dest"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
    throw "Missing SKILL.md for $name at $source"
  }
  foreach ($directory in @($source, $dest)) {
    if (Test-Path -LiteralPath $directory) {
      $links = @((Get-Item -LiteralPath $directory -Force); Get-ChildItem -LiteralPath $directory -Force -Recurse) |
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }
      if ($links) { throw "Linked content is not supported: $directory" }
    }
  }
  $files = @(Get-ChildItem -LiteralPath $source -File -Force -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($source.Length + 1)
    if (Test-PublicFile $relative) { @{ Source = $_.FullName; Relative = $relative } }
  })
  @{ Name = $name; Destination = $dest; Files = $files }
}

foreach ($entry in $plan) {
  $dest = $entry.Destination
  if (-not $PSCmdlet.ShouldProcess($dest, "Replace exported skill with filtered local sources")) { continue }
  if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Recurse -Force }
  New-Item -ItemType Directory -Path $dest -Force | Out-Null
  foreach ($file in $entry.Files) {
    $target = Join-Path $dest $file.Relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $file.Source -Destination $target -Force
  }
  Write-Host "Synced $($entry.Name): $($entry.Files.Count) public source files"
}

Write-Host "Done. Review the diff and public-file exclusions before committing."
