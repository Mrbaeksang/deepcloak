<div align="center">

# 🛡️ DeepCloak

### 봇 차단(Cloudflare·Datadome·Turnstile·reCAPTCHA) 뒤 페이지까지 읽는 딥리서치 에이전트.

[![CI](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml/badge.svg)](https://github.com/Mrbaeksang/deepcloak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![MCP native](https://img.shields.io/badge/MCP-native-8A2BE2.svg)](#ai-에이전트에서-쓰기-mcp)

[English](README.md) · **한국어** · [简体中文](README.zh-CN.md)

</div>

---

다른 로컬 딥리서치 툴은 첫 **Bot Wall**(봇 차단)에서 멈춘다. 중요한 소스가 Cloudflare 뒤에 있으면? `403` 받고 그 소스를 조용히 버린 뒤 더 얇은 리포트를 건넨다 — 뭘 놓쳤는지 너는 알 수도 없다.

**DeepCloak은 안 그런다.** plain fetch가 Bot Wall에 막히면 그 URL을 **Stealth Fetch**로 **에스컬레이트**해 벽을 **Bypass**(우회)하고, 몇 개의 소스를 뚫었는지까지 알려준다.

두 좋은 프로젝트 위의 얇은 오케스트레이터다: [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research)(리서치 루프) + [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser)(스텔스 브라우저). 로컬 우선, MIT, **CLI·MCP 서버·Claude 스킬**로 사용.

## ✨ 뭐가 다른가

|                              | 일반 딥리서치 | **DeepCloak** |
| ---------------------------- | :----------: | :-----------: |
| 열린 웹 읽기                  |      ✅       |       ✅       |
| Cloudflare/Datadome/Turnstile/reCAPTCHA 페이지 | ❌ (조용히 버림) | ✅ **Bypass** |
| 어떤 소스가 막혔는지 알려줌    | ❌ | ✅ Evidence Record |
| 로컬 우선 (API 키 불필요)     | ✅ | ✅ |
| 열린 페이지는 빠르게 (필요할 때만 스텔스) | — | ✅ plain 우선, 감지 시 에스컬레이트 |

> **라이브 검증:** `local-deep-research==1.6.11` + `cloakbrowser==0.3.31`에서 `nowsecure.nl`의 Cloudflare **Turnstile**을 ~5초에 Bypass, 열린 페이지(`example.com`)는 빠른 plain 경로(~0.1초) 유지. [`showcase/sample/evidence.json`](showcase/sample/evidence.json) 참고.

## 🚀 빠른 시작

```bash
pip install deepcloak
deepcloak setup                       # 스텔스 브라우저 내려받기
export OPENAI_API_KEY=...             # 또는 ANTHROPIC_API_KEY / GEMINI_API_KEY — 또는 --provider ollama
deepcloak "Cloudflare Turnstile은 봇을 어떻게 감지하나?" --depth detailed --out report.md
```

`report.md`(인용 포함, 끝에 `🛡️ Bypassed N bot-walled sources` 섹션) + `report.md.evidence.json` 사이드카가 생긴다.

## 🧠 작동 방식

```
검색 (DuckDuckGo, 설정 불필요) ──► 후보 URL
        │
        ▼
   페이지마다:  plain fetch ──► Bot Wall 감지? ──아니오──► 사용
                                     │ 예
                                     ▼
                               에스컬레이트 → Stealth Fetch(CloakBrowser) → Bypass
        │
        ▼
리서치 루프 (local-deep-research)  ──►  인용 리포트 + Evidence Records
```

스텔스는 무거워서, 먼저 싼 plain fetch를 하고 **Bot Wall을 실제로 감지했을 때만** 스텔스 브라우저를 띄운다(`--stealth auto`, 기본). `--stealth always`로 강제, `--stealth off`로 비활성.

> **깊이가 중요:** `--depth detailed`/`report`는 풀페이지를 가져온다(여기서 Bypass 발생). `--depth quick`은 스니펫 기반이라 풀페이지를 거의 안 가져온다.

## 🤖 AI 에이전트에서 쓰기 (MCP)

```bash
deepcloak mcp        # stdio MCP 서버
```

도구: `deep_research(query, depth)`, `quick_summary(query)`, `get_evidence(run_id)`. 또는 동봉된 [`skill/SKILL.md`](skill/SKILL.md)를 `~/.claude/skills/deepcloak/`에 넣어 Claude 스킬로 사용.

## ⚙️ 설정

| 플래그 | 기본값 | 비고 |
| --- | --- | --- |
| `--depth` | `detailed` | `quick` / `detailed` / `report` |
| `--engine` | `duckduckgo` | `searxng` / `auto` |
| `--stealth` | `auto` | `always` / `off` |
| `--provider` / `--model` | 자동감지 | `OPENAI_API_KEY` → `ANTHROPIC_API_KEY` → `GEMINI_API_KEY`, 또는 `ollama` |
| `--respect-robots` | 끔 | robots.txt 존중 |
| `--proxy` | — | Stealth Fetch용 SOCKS5 |

## ⚠️ 책임 있는 사용

DeepCloak은 봇 감지를 Bypass한다. **가져오는 콘텐츠에 접근할 권리는 너의 책임이다.** robots.txt는 **기본적으로 무시**되며, `--respect-robots`로 존중할 수 있다([ADR-0002](docs/adr/0002-ignore-robots-by-default.md)). 사이트 약관이나 법을 어기는 데 쓰지 말 것.

## 📄 라이선스 & 크레딧

MIT — [LICENSE](LICENSE) 참고. [`local-deep-research`](https://github.com/LearningCircuit/local-deep-research) + [`CloakBrowser`](https://github.com/CloakHQ/CloakBrowser)(둘 다 MIT) 기반, [NOTICE](NOTICE) 참고. 용어집은 [CONTEXT.md](CONTEXT.md), 설계 결정은 [docs/adr/](docs/adr/).
