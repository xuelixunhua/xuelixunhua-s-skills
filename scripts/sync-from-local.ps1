$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$skillsRoot = Join-Path $repoRoot "skills"
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null

$sources = @(
  @{ Name = "bggg-skill-taotie"; Source = Join-Path $HOME ".codex\skills\bggg-skill-taotie" },
  @{ Name = "content-master"; Source = Join-Path $HOME ".codex\skills\content-master" },
  @{ Name = "creator-content-knowledge-pipeline"; Source = Join-Path $HOME ".codex\skills\creator-content-knowledge-pipeline" },
  @{ Name = "llm-wiki-workspace"; Source = Join-Path $HOME ".codex\skills\llm-wiki-workspace" },
  @{ Name = "primitive-thinking"; Source = Join-Path $HOME ".codex\skills\primitive-thinking" },
  @{ Name = "research-synthesis"; Source = Join-Path $HOME ".codex\skills\research-synthesis" },
  @{ Name = "web-access"; Source = Join-Path $HOME ".codex\skills\web-access" },
  @{ Name = "skill-creator"; Source = Join-Path $HOME ".agents\skills\skill-creator" }
)

foreach ($entry in $sources) {
  if (-not (Test-Path -LiteralPath $entry.Source)) {
    Write-Warning "Missing source for $($entry.Name): $($entry.Source)"
    continue
  }

  $dest = Join-Path $skillsRoot $entry.Name
  if (Test-Path -LiteralPath $dest) {
    Remove-Item -LiteralPath $dest -Recurse -Force
  }

  Copy-Item -LiteralPath $entry.Source -Destination $dest -Recurse -Force

  foreach ($cacheDir in @("__pycache__", "node_modules")) {
    Get-ChildItem -LiteralPath $dest -Recurse -Directory -Force |
      Where-Object { $_.Name -eq $cacheDir } |
      ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
  }

  if ($entry.Name -eq "web-access") {
    $skillIgnore = Join-Path $dest ".gitignore"
    if (Test-Path -LiteralPath $skillIgnore) {
      $lines = Get-Content -LiteralPath $skillIgnore | Where-Object { $_ -ne "references/site-patterns/*.md" }
      Set-Content -LiteralPath $skillIgnore -Value $lines -Encoding UTF8
    }
  }

  Write-Host "Synced $($entry.Name)"
}

Write-Host "Done. Review with git status before committing."
