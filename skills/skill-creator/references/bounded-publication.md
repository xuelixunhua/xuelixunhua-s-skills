# Bounded publication after skill maintenance

Use this closeout after a delegated modification to a maintained skill has been completed and validated. For this maintainer, the public repository is https://github.com/xuelixunhua/xuelixunhua-s-skills; the maintained sources are under `~/.codex/skills`. The latest repository `manifest.json` is the publication whitelist. Do not infer that every installed skill is public.

## Scope and authority

- Track the files changed for the current task against their pre-edit state. Select only the modified skills that are in the whitelist; a ten-skill whitelist does not authorize publishing every pending local change.
- Check the current request or an applicable, explicitly granted continuing authorization for public commit/push. This document and skill loading do not grant publishing authority. A request to prepare only, missing authority, changed visibility/destination, sensitive content, or a material scope/risk change leaves the work ready for review or pending publication; report the concrete gap.
- Run once at the end of the delegated maintenance task. Do not watch arbitrary manual saves, create scheduled jobs, or install a background service.

## Publish the reviewed task changes

1. Check the actual remote URL, visibility, latest `main` SHA, and working-tree state. Use a clean isolated checkout from latest `main`; preserve older worktrees and their edits. A fresh clone also avoids same-tree/different-commit divergence after an API-based publication.
2. Use the repository's existing `scripts/sync-from-local.ps1 -Skills <selected names> -WhatIf`, then export only those names. Read the current script and manifest before running it. Export replaces selected repository copies, so never run it over unprotected edits.
3. Review every resulting modified, added, and deleted file against latest `main`, including untracked files. A selected skill can contain pre-existing unrelated edits: exclude those hunks/files from the isolated candidate, or report an inseparable dependency for review. Do not overwrite the maintained source to force it to match the public copy.
4. Check public suitability: private paths, real accounts, credentials, session-bearing URLs, personal/customer data, licensing, local configuration, generated results, and unrelated internal material. Keep the existing public-file filters. Use generic home-relative examples, such as `$SkillRoot = Join-Path $HOME '.codex\skills\web-access'`; recheck both `web-access/README.md` and `web-access/references/cdp-api.md` whenever exported. Filtering filenames alone does not sanitize file contents.
5. Run `git diff --check`, the changed skills' relevant validation, and appropriate repository tests. Record the exact reviewed paths and content hashes. Remove line-ending-only noise without discarding substantive edits. No change means no commit.
6. With effective publishing authorization and a reviewed candidate, stage only the exact approved paths/hunks; inspect the staged diff, commit, and push without force. Recheck remote `main` immediately before updating it. If the base changed, reconcile in isolation and repeat affected review/validation; never overwrite it blindly.
7. If Git transport fails, a connected authorized GitHub tool may publish the same reviewed content: create blobs, build on the verified base tree, verify the complete tree SHA against the local commit, create a commit with the verified parent, then update `main` with `force=false`. Stop on approval rejection or missing connection; do not read or transfer credentials to work around it.
8. Read back remote commit/tree, verify exact content, working-tree state, and available CI. Report the commit link and any failed or unavailable verification. Do not report publication complete from a local commit alone.

## Existing commands

From the clean isolated repository, pass an explicit PowerShell array of this task's selected names:

```powershell
$selectedSkills = @('content-master') # Replace with this task's actual whitelist intersection.
.\scripts\sync-from-local.ps1 -Skills $selectedSkills -WhatIf
.\scripts\sync-from-local.ps1 -Skills $selectedSkills
git diff --check
git status --short
git diff
```

The repository README documents its test commands. Resolve a working Python interpreter with required dependencies; do not assume a Windows application alias runs Python. Review untracked files separately because `git diff` omits them. Use an exact reviewed path list with `git add --`, not `git add .`. Do not rerun export after review without rebuilding and rechecking the candidate.
