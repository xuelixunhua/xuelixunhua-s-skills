# CDP Proxy API 参考（Windows / PowerShell）

## 基础信息

- 地址：`http://localhost:3456`
- 仅在任务确实需要 CDP 时启动：`$SkillRoot = 'C:\Users\xueli\.codex\skills\web-access'; node "$SkillRoot\scripts\check-deps.mjs"`
- 前置检查负责启动和复用 Proxy；不要另起一个实例，也不要为了清理主动停止已复用的 Proxy
- 支持 Chrome、Edge 和 Chromium；默认只操作 Agent 自己创建的后台 tab
- PowerShell 中一律使用 `curl.exe`，避免 `curl` 被映射为 `Invoke-WebRequest`

## API 端点

### GET /health
健康检查，返回连接状态。
```powershell
curl.exe -s http://localhost:3456/health
```

### GET /targets
列出所有已打开的页面 tab。返回数组，每项含 `targetId`、`title`、`url`。
```powershell
curl.exe -s http://localhost:3456/targets
```

### POST /new
创建新后台 tab，自动等待页面加载完成。**URL 通过 POST body 原样传入**，无需 URL-encode、不会因 query 中含 `&` 被切分。返回 `{ targetId }`。
```powershell
curl.exe -s -X POST --data-raw 'https://example.com' http://localhost:3456/new
# 含 query 的目标 URL（如带 token 的小红书笔记）也直接原样传：
curl.exe -s -X POST --data-raw 'https://www.xiaohongshu.com/explore/xxx?xsec_source=app_share&xsec_token=ABC&type=normal' http://localhost:3456/new
```
> v2.5.3 起改为 POST。旧的 `GET /new?url=...` 返回 400 + 迁移指引，详见 `migration-2.5.3.md`。

### GET /close?target=ID
关闭指定 tab。
```powershell
curl.exe -s "http://localhost:3456/close?target=TARGET_ID"
```

### POST /navigate?target=ID
在已有 tab 中导航到新 URL，自动等待加载。**target 走 query（不带特殊字符的不透明 ID），URL 走 POST body**。
```powershell
curl.exe -s -X POST --data-raw 'https://example.com' "http://localhost:3456/navigate?target=ID"
```
> v2.5.3 起改为 POST。旧的 `GET /navigate?target=...&url=...` 返回 400 + 迁移指引，详见 `migration-2.5.3.md`。

### GET /back?target=ID
后退一页。
```powershell
curl.exe -s "http://localhost:3456/back?target=ID"
```

### GET /info?target=ID
获取页面基础信息（title、url、readyState）。
```powershell
curl.exe -s "http://localhost:3456/info?target=ID"
```

### POST /eval?target=ID
执行 JavaScript 表达式，POST body 为 JS 代码。
```powershell
curl.exe -s -X POST "http://localhost:3456/eval?target=ID" -d 'document.title'
```

### POST /click?target=ID
JS 层面点击（`el.click()`），POST body 为 CSS 选择器。自动 scrollIntoView 后点击。简单快速，覆盖大多数场景。
```powershell
curl.exe -s -X POST "http://localhost:3456/click?target=ID" -d 'button.submit'
```

### POST /clickAt?target=ID
CDP 浏览器级真实鼠标点击（`Input.dispatchMouseEvent`），POST body 为 CSS 选择器。先获取元素坐标，再模拟鼠标按下/释放。算真实用户手势，能触发文件对话框、绕过部分反自动化检测。
```powershell
curl.exe -s -X POST "http://localhost:3456/clickAt?target=ID" -d 'button.upload'
```

### POST /setFiles?target=ID
给 file input 设置本地文件路径（`DOM.setFileInputFiles`），完全绕过文件对话框。POST body 为 JSON。
```powershell
curl.exe -s -X POST "http://localhost:3456/setFiles?target=ID" -d '{"selector":"input[type=file]","files":["/path/to/file1.png","/path/to/file2.png"]}'
```

### GET /scroll?target=ID&y=3000&direction=down
滚动页面。`direction` 可选 `down`（默认）、`up`、`top`、`bottom`。滚动后自动等待 800ms 供懒加载触发。
```powershell
curl.exe -s "http://localhost:3456/scroll?target=ID&y=3000"
curl.exe -s "http://localhost:3456/scroll?target=ID&direction=bottom"
```

### GET /screenshot?target=ID&file=PATH
截图。指定 `file` 参数保存到本地文件；不指定则返回图片二进制。Windows 上可直接让 `curl.exe` 把二进制写入 `%TEMP%`。可选 `format=jpeg`。
```powershell
curl.exe -s "http://localhost:3456/screenshot?target=ID" -o "$env:TEMP\web-access-shot.png"
```

## /eval 使用提示

- POST body 为任意 JS 表达式，返回 `{ value }` 或 `{ error }`
- 支持 `awaitPromise`：可以写 async 表达式
- 返回值必须是可序列化的（字符串、数字、对象），DOM 节点不能直接返回，需要提取属性
- 提取大量数据时用 `JSON.stringify()` 包裹，确保返回字符串
- 根据页面实际 DOM 结构编写选择器，不要套用固定模板

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| 浏览器未开启远程调试 | 选定浏览器的调试开关未启用 | 提示用户打开 Chrome 或 Edge 对应的 inspect 页面并勾选 Allow |
| `browser: needs decision` | 同时存在多个可用浏览器且没有偏好 | 询问用户选择，不自行写入 `config.env` 或静默切换浏览器 |
| `attach 失败` | targetId 无效或 tab 已关闭 | 用 `/targets` 获取最新列表 |
| `CDP 命令超时` | 页面长时间未响应 | 重试或检查 tab 状态 |
| `端口已被占用` | 另一个 proxy 已在运行 | 已有实例可直接复用 |
