param(
  [string[]]$Skills,
  [string]$Destination = (Join-Path $HOME ".codex\skills"),
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$sourceRoot = Join-Path $repoRoot "skills"

if (-not (Test-Path -LiteralPath $sourceRoot)) {
  throw "Missing skills directory: $sourceRoot"
}

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

$available = Get-ChildItem -LiteralPath $sourceRoot -Directory | Sort-Object Name
if ($Skills -and $Skills.Count -gt 0) {
  $wanted = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach ($skill in $Skills) { [void]$wanted.Add($skill) }
  $available = $available | Where-Object { $wanted.Contains($_.Name) }
}

foreach ($skillDir in $available) {
  $skillFile = Join-Path $skillDir.FullName "SKILL.md"
  if (-not (Test-Path -LiteralPath $skillFile)) {
    Write-Warning "Skipping $($skillDir.Name): missing SKILL.md"
    continue
  }

  $target = Join-Path $Destination $skillDir.Name
  if (Test-Path -LiteralPath $target) {
    if (-not $Force) {
      Write-Warning "Skipping $($skillDir.Name): already exists at $target. Use -Force to overwrite."
      continue
    }
    Remove-Item -LiteralPath $target -Recurse -Force
  }

  Copy-Item -LiteralPath $skillDir.FullName -Destination $target -Recurse -Force
  Write-Host "Installed $($skillDir.Name) -> $target"
}

Write-Host "Done. Restart Codex to pick up installed skills."

