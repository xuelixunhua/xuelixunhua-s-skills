# web-access for Codex on Windows

This is a local Codex adaptation of [eze-is/web-access](https://github.com/eze-is/web-access), based on upstream commit `7af34af` (v2.5.3).

The active control plane is [`SKILL.md`](SKILL.md). It keeps the upstream browser/CDP model while adapting routing and commands for this machine:

- Public web research starts with Codex native Web tools. CDP is only an escalation path for login state, dynamic DOM, real interaction, or reliably blocked static access.
- CDP uses Chrome, Edge, or Chromium with remote debugging enabled.
- PowerShell examples use `curl.exe`, not the `curl` alias.
- URLs for `/new` and `/navigate` go in the POST body so query parameters, fragments, and site tokens are preserved.
- Browser history and bookmarks are only searched for an explicit user request and are treated as private local data.

## Local layout

| Path | Purpose |
|---|---|
| `SKILL.md` | Triggering, routing, safety, and completion rules |
| `scripts/check-deps.mjs` | Browser discovery, preference check, and proxy startup |
| `scripts/cdp-proxy.mjs` | CDP proxy with agent-created tab lifecycle |
| `scripts/find-url.mjs` | Explicit lookup of Chrome/Edge bookmarks or history |
| `scripts/match-site.mjs` | Match local, verified site-pattern notes |
| `references/cdp-api.md` | PowerShell API reference |
| `references/migration-2.5.3.md` | POST-body URL migration note |

## CDP setup

Only when a task needs CDP, run:

```powershell
$SkillRoot = 'C:\Users\xueli\.codex\skills\web-access'
node "$SkillRoot\scripts\check-deps.mjs"
```

Enable remote debugging in the browser you intend to use:

- Chrome: `chrome://inspect/#remote-debugging`
- Edge: `edge://inspect/#remote-debugging`

The first run can create a local `config.env`. It is ignored by Git and records no preference until the user chooses one.

Node.js 22+ is preferred. This installation retains the `ws` dependency so the CDP proxy can run on the current Node 20 runtime.

## Updating

When upstream changes, inspect the release or main commit first. Sync deterministic scripts and API migrations only after reviewing them; keep Codex routing, Windows-specific commands, privacy boundaries, and verified local site patterns intact.
