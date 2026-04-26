---
domain: mp.weixin.qq.com
aliases: [微信公众号, 微信公众平台, WeChat MP]
updated: 2026-04-12
---
## 平台特征
- 公众平台后台接口依赖登录态，静态直连容易缺 cookie / token；复用已登录 Chrome tab 最稳。
- `mp.weixin.qq.com/cgi-bin/appmsg?...token=...` 编辑页 URL 中可直接拿到 `token`。
- 在编辑器中选择“账号文章 -> 选择其他账号”时，页面本质上会走后台接口查询公众号与历史文章。

## 有效模式
- 先在已登录的 `mp.weixin.qq.com` page target 上通过 `/eval` 执行带 `credentials: 'include'` 的 `fetch(...)`。
- 公众号搜索接口：
  `https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&token=TOKEN&lang=zh_CN&f=json&ajax=1&begin=0&count=5&query=公众号名`
- 历史文章列表接口：
  `https://mp.weixin.qq.com/cgi-bin/appmsg?token=TOKEN&lang=zh_CN&f=json&ajax=1&action=list_ex&begin=0&count=5&query=&fakeid=FAKEID&type=9`
- `searchbiz` 返回的 `list[0].fakeid` 可直接喂给 `appmsg?action=list_ex`。
- `appmsg?action=list_ex` 返回 `app_msg_cnt` 和 `app_msg_list`；每页 5 条，`begin` 递增分页即可。
- 返回的 `app_msg_list[].link` 是公开文章页，可再用普通 HTTP 请求下载 HTML / 提取正文。

## 已知陷阱
- Windows 上如果照 skill 文档直接跑 `check-deps.sh`，可能因为本机未装 WSL / bash 而失败；这时直接检查 `http://localhost:3456/targets` 是否可用即可。
- 直接拼后台接口但不走当前登录 tab 的 cookie 上下文，容易返回未登录或异常结果。
- `rg` 在某些 WindowsApp 安装环境下可能无法从当前工作目录启动，必要时改用 PowerShell 自带检索。
