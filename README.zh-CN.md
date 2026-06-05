<div align="center">

<h1>🛡️ DeepCloak</h1>

### 能读取别人读不到的页面的深度研究智能体。

**Cloudflare · Datadome · Turnstile · reCAPTCHA —— 直接穿过它们，把正文带回来。**

[![CI](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml/badge.svg)](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-a855f7.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![MCP native](https://img.shields.io/badge/MCP-native-22d3ee.svg)](#-在-ai-智能体中使用)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-34d399.svg)](CONTRIBUTING.md)
[![GitHub stars](https://img.shields.io/github/stars/Mrbaeksang/deepcloak?style=social)](https://github.com/Mrbaeksang/deepcloak/stargazers)

[English](README.md) · [한국어](README.ko.md) · **简体中文**

### [▶ 在线演示 — deepcloak.vercel.app](https://deepcloak.vercel.app)  ·  [▶ 在 YouTube 观看](https://youtu.be/MMqz-UMWtSI)

[![DeepCloak 运行：检测 Cloudflare Turnstile → 升级 → 绕过 → 生成带引用的报告](docs/media/demo.gif)](https://youtu.be/MMqz-UMWtSI)

</div>

---

## 问题

你向研究工具提问。可一半的优质来源都藏在 **Bot Wall（机器人拦截）** 后面 —— Cloudflare、Datadome、Turnstile、reCAPTCHA。其他工具拿到 `403`，悄悄丢掉这些页面，给你一份更单薄的报告。**而且根本不告诉你漏掉了什么。**

## DeepCloak 做的事

当普通抓取撞上 Bot Wall，DeepCloak 会把这一个 URL **升级为隐身抓取（Stealth Fetch）**，**绕过（Bypass）** 拦截，找回其他智能体放弃的正文。然后在每份报告末尾，准确告诉你它突破了多少道墙。

它是构建在两个优秀项目之上的轻量、本地优先编排器：[`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)（研究循环）+ [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser)（隐身浏览器）。可作为 **CLI、MCP 服务器、Claude 技能** 使用。MIT。

## 🌑 我们为何要做它

开放的网络正在悄悄关闭。越来越多优质内容躲到机器人验证之后，而我们越来越信任、让它替我们读网页的 AI 研究智能体，**恰恰在那些门前失明 —— 而且一声不吭。** 一份悄悄跳过所有被拦来源的报告并非中立，而是以你看不见的方式出错。

DeepCloak 的立场很简单：**浏览器前的人能读到的，你的智能体也应该能读到** —— 并且要对如何读到坦诚。所以它在必要时绕过墙，全部本地处理（查询与页面都不外传），并以证据记录展示它跨过的每一道墙。能力*与*透明并存，MIT 许可，无锁定。

## ✨ 有何不同

|  | 普通深度研究 | **DeepCloak** |
| --- | :---: | :---: |
| 读取开放网页 | ✅ | ✅ |
| 读取 Cloudflare/Datadome/Turnstile/reCAPTCHA 页面 | ❌ *悄悄丢弃* | ✅ **绕过** |
| 告诉你哪些来源被拦 | ❌ | ✅ 证据记录 |
| 本地优先（无需 API 密钥） | ✅ | ✅ |
| 开放页面更快 | — | ✅ *先普通抓取，仅在需要时隐身* |

> **实测验证 —— 非演示造假。** 上方视频是用 `ffmpeg` 录制的真实 `deepcloak` 运行的**未剪辑屏幕录像**（无合成）—— **本地 LLM（Qwen）+ SearXNG，无需 API 密钥**。它在每道 Bot Wall 上升级，一次性 **绕过 8 道 Cloudflare/Turnstile 墙**，再写出带引用的报告。完整片段：[`docs/media/demo-real.mp4`](docs/media/demo-real.mp4)，原始 asciinema 会话也保留在 [`docs/media/demo.cast`](docs/media/demo.cast)。每次运行墙的数量不同（8–20），因为开放网络本就如此。

## 🚀 快速开始

```bash
pip install deepcloak
deepcloak setup                       # 一次性：下载隐身浏览器
export OPENAI_API_KEY=...             # 或 ANTHROPIC_API_KEY / GEMINI_API_KEY —— 或 --provider ollama
deepcloak "Cloudflare Turnstile 如何检测机器人？" --depth detailed --out report.md
```

你会得到带引用的 `report.md`（末尾有 `🛡️ Bypassed N bot-walled sources`）以及 `report.md.evidence.json` 附属文件。

## 🧠 工作原理

```
搜索 (DuckDuckGo, 无需配置) ─▶ 候选 URL
        │
        ▼  每个页面:
   普通抓取 ─▶ 检测到 Bot Wall? ──否──▶ 直接使用 (快)
                        │ 是
                        ▼
                  升级 ─▶ 隐身抓取 (CloakBrowser) ─▶ 绕过
        │
        ▼
研究循环 (local-deep-research) ─▶ 带引用的报告 + 证据记录
```

隐身开销大，所以先尝试廉价的普通抓取，**仅在真正检测到 Bot Wall 时** 才启动隐身浏览器（`--stealth auto`，默认）。用 `--depth detailed`/`report` 抓取完整页面（绕过发生在此）。

## 🤖 接入你的智能体 (MCP)

DeepCloak 作为 stdio **MCP 服务器** 运行，暴露 `deep_research(query, depth)`、`quick_summary(query)`、`get_evidence(run_id)`。

**Claude Code** — 加入项目的 `.mcp.json`（仓库内含示例）：

```json
{ "mcpServers": { "deepcloak": { "command": "deepcloak", "args": ["mcp"] } } }
```

**Codex** — 加入 `~/.codex/config.toml`：

```toml
[mcp_servers.deepcloak]
command = "deepcloak"
args = ["mcp"]
```

然后智能体即可调用 `deep_research`，直接读取被拦截的来源。想用斜杠技能？把 [`skill/SKILL.md`](skill/SKILL.md) 放入 `~/.claude/skills/deepcloak/`。

## ⚙️ 配置

| 选项 | 默认 | 说明 |
| --- | --- | --- |
| `--depth` | `detailed` | `quick` / `detailed` / `report` |
| `--engine` | `duckduckgo` | `searxng` / `auto` |
| `--stealth` | `auto` | `always` / `off` |
| `--provider` / `--model` | 自动检测 | `OPENAI` → `ANTHROPIC` → `GEMINI`，或 `ollama` |
| `--respect-robots` | 关 | 遵守 robots.txt |
| `--proxy` | — | 隐身抓取使用的 SOCKS5 |

## ⚠️ 负责任地使用

DeepCloak 会绕过机器人检测。**你有责任确保自己有权访问所抓取的内容。** robots.txt **默认被忽略**，可用 `--respect-robots` 遵守（[ADR-0002](docs/adr/0002-ignore-robots-by-default.md)）。请勿用于违反网站条款或法律。

## 🛠️ 构建于

[`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)（MIT）+ [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser)（MIT），通过 pip 依赖 —— 不内嵌代码。术语表 [CONTEXT.md](CONTEXT.md)，设计决策 [docs/adr/](docs/adr/)，贡献指南 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 许可

MIT —— 见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。

<div align="center">

**如果 DeepCloak 读到了上一个工具放弃的页面，点个 ⭐ —— 能帮更多人发现它。**

[![Star History Chart](https://api.star-history.com/svg?repos=Mrbaeksang/deepcloak&type=Date)](https://star-history.com/#Mrbaeksang/deepcloak&Date)

</div>
