# v2.5.3 CDP URL Migration

The proxy now sends target URLs through the POST body. The old GET forms can cut URLs at `&`, drop fragments, and lose token-bearing parameters.

```powershell
# Old
curl.exe -s "http://localhost:3456/new?url=https://example.com/path?a=1&b=2"

# New
curl.exe -s -X POST --data-raw 'https://example.com/path?a=1&b=2' http://localhost:3456/new

# Old
curl.exe -s "http://localhost:3456/navigate?target=TARGET_ID&url=https://example.com/path?a=1&b=2"

# New
curl.exe -s -X POST --data-raw 'https://example.com/path?a=1&b=2' "http://localhost:3456/navigate?target=TARGET_ID"
```

When an old call appears in a site pattern, script, or note, change the source artifact as well as the current command. Preserve the target URL exactly as obtained from the site.
