<div align="center">

# 🛡️ DeepCloak

### 能读取整个网络的深度研究智能体 —— 连 Cloudflare、Datadome、Turnstile、reCAPTCHA 背后的页面也能读。

[![CI](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml/badge.svg)](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![MCP native](https://img.shields.io/badge/MCP-native-8A2BE2.svg)](#在-ai-智能体中使用-mcp)

[English](README.md) · [한국어](README.ko.md) · **简体中文**

</div>

---

其他本地深度研究工具都止步于第一道 **Bot Wall**（机器人拦截）。相关来源藏在 Cloudflare 后面？它拿到 `403`，悄悄丢掉该来源，给你一份更单薄的报告 —— 而你根本不知道漏掉了什么。

**DeepCloak 不会这样。** 当普通抓取撞上 Bot Wall 时，它会把该 URL **升级（Escalate）** 为 **隐身抓取（Stealth Fetch）**，**绕过（Bypass）** 拦截，并明确告诉你它突破了多少个来源。

它是构建在两个优秀项目之上的轻量编排器：[`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)（研究循环）+ [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser)（隐身浏览器）。本地优先、MIT 许可，可作为 **CLI、MCP 服务器和 Claude 技能** 使用。

## ✨ 有何不同

|                              | 普通深度研究 | **DeepCloak** |
| ---------------------------- | :----------: | :-----------: |
| 读取开放网页                  |      ✅       |       ✅       |
| 读取 Cloudflare/Datadome/Turnstile/reCAPTCHA 页面 | ❌（悄悄丢弃） | ✅ **绕过** |
| 告诉你哪些来源被拦截          | ❌ | ✅ 证据记录 |
| 本地优先（无需 API 密钥）     | ✅ | ✅ |
| 开放页面快速处理（仅在需要时隐身） | — | ✅ 先普通抓取，检测到才升级 |

> **实测验证：** 在 `local-deep-research==1.6.11` + `cloakbrowser==0.3.31` 上，DeepCloak 约 5 秒绕过 `nowsecure.nl` 的 Cloudflare **Turnstile**，而开放页面（`example.com`）保持在快速普通路径（约 0.1 秒）。见 [`showcase/sample/evidence.json`](showcase/sample/evidence.json)。

## 🚀 快速开始

```bash
pip install deepcloak
deepcloak setup                       # 下载隐身浏览器
export OPENAI_API_KEY=...             # 或 ANTHROPIC_API_KEY / GEMINI_API_KEY —— 或 --provider ollama
deepcloak "Cloudflare Turnstile 如何检测机器人？" --depth detailed --out report.md
```

你会得到 `report.md`（带引用，结尾有 `🛡️ Bypassed N bot-walled sources` 部分）以及 `report.md.evidence.json` 附属文件。

## 🧠 工作原理

```
搜索 (DuckDuckGo, 无需配置) ──► 候选 URL
        │
        ▼
   每个页面:  普通抓取 ──► 检测到 Bot Wall? ──否──► 直接使用
                                  │ 是
                                  ▼
                            升级 → 隐身抓取(CloakBrowser) → 绕过
        │
        ▼
研究循环 (local-deep-research)  ──►  带引用的报告 + 证据记录
```

隐身开销大，所以 DeepCloak 先尝试廉价的普通抓取，**仅在真正检测到 Bot Wall 时** 才启动隐身浏览器（`--stealth auto`，默认）。用 `--stealth always` 强制，`--stealth off` 关闭。

> **深度影响绕过：** `--depth detailed`/`report` 会抓取完整页面（绕过发生在此）；`--depth quick` 基于摘要，很少抓取完整页面。

## 🤖 在 AI 智能体中使用 (MCP)

```bash
deepcloak mcp        # stdio MCP 服务器
```

工具：`deep_research(query, depth)`、`quick_summary(query)`、`get_evidence(run_id)`。或将自带的 [`skill/SKILL.md`](skill/SKILL.md) 放入 `~/.claude/skills/deepcloak/` 作为 Claude 技能使用。

## ⚙️ 配置

| 选项 | 默认 | 说明 |
| --- | --- | --- |
| `--depth` | `detailed` | `quick` / `detailed` / `report` |
| `--engine` | `duckduckgo` | `searxng` / `auto` |
| `--stealth` | `auto` | `always` / `off` |
| `--provider` / `--model` | 自动检测 | `OPENAI_API_KEY` → `ANTHROPIC_API_KEY` → `GEMINI_API_KEY`，或 `ollama` |
| `--respect-robots` | 关 | 遵守 robots.txt |
| `--proxy` | — | 隐身抓取使用的 SOCKS5 |

## ⚠️ 负责任地使用

DeepCloak 会绕过机器人检测。**你有责任确保自己有权访问所抓取的内容。** robots.txt **默认被忽略**，可用 `--respect-robots` 遵守（[ADR-0002](docs/adr/0002-ignore-robots-by-default.md)）。请勿用于违反网站条款或法律。

## 📄 许可与致谢

MIT —— 见 [LICENSE](LICENSE)。基于 [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research) 与 [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser)（均为 MIT），见 [NOTICE](NOTICE)。术语表见 [CONTEXT.md](CONTEXT.md)，设计决策见 [docs/adr/](docs/adr/)。
