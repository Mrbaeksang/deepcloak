"use client";

import { motion } from "framer-motion";
import dynamic from "next/dynamic";
import { useState } from "react";
import evidence from "../data/evidence.json";
import { cn } from "../lib/utils";

const CosmicGlobe = dynamic(() => import("../components/CosmicGlobe"), { ssr: false });

const REPO = "https://github.com/Mrbaeksang/deepcloak";
const YOUTUBE = "https://youtu.be/MMqz-UMWtSI";

type Record = {
  url: string;
  bot_wall: string | null;
  escalated: boolean;
  bypassed: boolean;
  plain_status: number | null;
  elapsed_ms: number;
  signal: string | null;
};

const records = (evidence.records ?? []) as Record[];
const summary = evidence.summary ?? { total: 0, escalated: 0, bypassed: 0, walls: {} };
const turnstileMs = records.find((r) => r.bypassed)?.elapsed_ms ?? 0;

function Section({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={cn("relative z-10 mx-auto w-full max-w-3xl px-6", className)}
    >
      {children}
    </motion.section>
  );
}

const Eyebrow = ({ children }: { children: React.ReactNode }) => (
  <div className="text-xs font-medium uppercase tracking-[0.2em] text-cyber">{children}</div>
);

export default function Page() {
  const [lang, setLang] = useState<"en" | "ko">("en");

  return (
    <main className="flex flex-col items-center gap-32 pb-32">
      {/* Hero with cosmic globe */}
      <section className="relative flex min-h-[88vh] w-full flex-col items-center justify-center overflow-hidden px-6 text-center">
        <div className="pointer-events-none absolute inset-0 z-0 opacity-80">
          <CosmicGlobe />
        </div>
        <div className="relative z-10 flex flex-col items-center">
          <motion.div
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="text-7xl drop-shadow-[0_0_30px_rgba(133,59,206,0.6)]"
          >
            🛡️
          </motion.div>
          <h1 className="mt-5 text-5xl font-semibold tracking-tight sm:text-7xl">DeepCloak</h1>
          <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-muted">
            Deep research that reads the <span className="text-cyber">whole</span> web — even pages
            behind <span className="text-cloak">Cloudflare, Datadome, Turnstile &amp; reCAPTCHA</span>.
          </p>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <a
              href={REPO}
              className="rounded-sm bg-cloak px-6 py-3 font-medium text-white shadow-glow transition hover:brightness-110"
            >
              ★ Star on GitHub
            </a>
            <a
              href="#demo"
              className="rounded-sm border border-borderlit px-6 py-3 font-medium text-white/90 transition hover:border-cloak hover:text-white"
            >
              Watch the demo ↓
            </a>
            <a
              href={YOUTUBE}
              target="_blank"
              rel="noopener"
              className="rounded-sm border border-borderlit px-6 py-3 font-medium text-white/90 transition hover:border-red-500 hover:text-white"
            >
              ▶ YouTube
            </a>
          </div>
          <p className="mt-7 font-mono text-sm text-muted">pip install deepcloak</p>
        </div>
      </section>

      {/* Product demo — terminal run */}
      <Section className="text-center">
        <div id="demo" className="-mt-28 pt-28" />
        <Eyebrow>See it run</Eyebrow>
        <h2 className="mt-3 text-3xl font-semibold">A real run, end to end</h2>
        <div className="mx-auto mt-7 w-full max-w-2xl overflow-hidden rounded-lg border border-borderlit shadow-glow">
          <video className="w-full" src="/demo.mp4" autoPlay muted loop playsInline />
        </div>
        <p className="mx-auto mt-3 max-w-xl text-sm text-muted">
          An unedited screen recording — DeepCloak running against a local LLM (Qwen) + SearXNG,
          Escalating to a Stealth Fetch on each Bot Wall, Bypassing it, then writing a cited report
          ending with the 🛡️ Bypassed badge.
        </p>
        <a
          href={YOUTUBE}
          target="_blank"
          rel="noopener"
          className="mt-4 inline-block rounded-sm border border-borderlit px-4 py-2 text-sm text-white/90 transition hover:border-red-500"
        >
          ▶ Watch the full demo on YouTube
        </a>
      </Section>

      {/* 30-second promo (EN / KO) */}
      <Section className="text-center">
        <Eyebrow>30-second story</Eyebrow>
        <h2 className="mt-3 text-3xl font-semibold">The short</h2>
        <div className="mt-5 inline-flex items-center gap-1 rounded-sm border border-border bg-surface p-1">
          {(["en", "ko"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={cn(
                "rounded-sm px-4 py-1.5 text-sm font-medium transition",
                lang === l ? "bg-cloak text-white" : "text-muted hover:text-white"
              )}
            >
              {l === "en" ? "English" : "한국어"}
            </button>
          ))}
        </div>
        <div className="mx-auto mt-6 w-full max-w-[340px] overflow-hidden rounded-lg border border-borderlit shadow-glow">
          <video
            key={lang}
            className="w-full"
            src={lang === "en" ? "/promo-en.mp4" : "/promo-ko.mp4"}
            controls
            autoPlay
            muted
            loop
            playsInline
          />
        </div>
      </Section>

      {/* Stats */}
      <Section className="text-center">
        <div className="grid grid-cols-3 gap-3 sm:gap-4">
          {[
            { n: summary.bypassed, label: "Bot Walls bypassed", c: "text-cyber" },
            { n: summary.total, label: "sources fetched", c: "text-white" },
            { n: `${Math.round(turnstileMs / 100) / 10}s`, label: "to clear Turnstile", c: "text-cloak" },
          ].map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.85 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="rounded-md border border-border bg-surface/70 p-6"
            >
              <div className={cn("text-4xl font-semibold", s.c)}>{s.n}</div>
              <div className="mt-1 text-xs text-muted">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* Evidence timeline */}
      <Section>
        <div className="text-center">
          <Eyebrow>Evidence Record</Eyebrow>
          <h2 className="mt-3 text-3xl font-semibold">Every fetch, on the record</h2>
          <p className="mx-auto mt-2 max-w-lg text-sm text-muted">
            Plain fetch first; escalate to a stealth Bypass only when a Bot Wall is detected. Open
            pages stay fast.
          </p>
        </div>
        <div className="mt-9 flex flex-col gap-3">
          {records.map((r, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12 }}
              className={cn(
                "rounded-md border p-5",
                r.bypassed ? "border-cloak/60 bg-cloak/10" : "border-border bg-surface/60"
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="truncate font-mono text-sm">{r.url}</span>
                <span className="shrink-0 font-mono text-xs text-muted">{r.elapsed_ms} ms</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-sm">
                <span className="rounded-sm bg-slate2 px-2 py-0.5 text-white/80">plain → {r.plain_status ?? "—"}</span>
                {r.bot_wall && r.bot_wall !== "forced" ? (
                  <>
                    <span className="text-borderlit">→</span>
                    <span className="rounded-sm bg-red-500/20 px-2 py-0.5 text-red-300">🧱 {r.bot_wall}</span>
                  </>
                ) : null}
                {r.escalated ? (
                  <>
                    <span className="text-borderlit">→</span>
                    <span className="rounded-sm bg-cyber/15 px-2 py-0.5 text-cyber">⚡ escalate</span>
                  </>
                ) : null}
                <span className="text-borderlit">→</span>
                {r.bypassed ? (
                  <span className="rounded-sm bg-cloak/25 px-2 py-0.5 text-purple-200">✅ bypassed</span>
                ) : (
                  <span className="rounded-sm bg-green-500/10 px-2 py-0.5 text-green-200/80">✓ open page</span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* How it works */}
      <Section className="text-center">
        <Eyebrow>How it works</Eyebrow>
        <div className="mt-7 flex flex-col items-stretch gap-3 text-left sm:flex-row sm:items-center sm:justify-center">
          {["🔎 search", "🌐 plain fetch", "🧱 Bot Wall?", "⚡ Stealth Fetch", "📄 cited report"].map(
            (step, i, arr) => (
              <div key={i} className="flex items-center gap-3">
                <div className="rounded-sm border border-border bg-surface/60 px-4 py-3 text-sm">{step}</div>
                {i < arr.length - 1 ? <span className="hidden text-cloak sm:inline">→</span> : null}
              </div>
            )
          )}
        </div>
        <p className="mx-auto mt-6 max-w-lg text-sm text-muted">
          Built on <span className="text-white">local-deep-research</span> and{" "}
          <span className="text-white">CloakBrowser</span>. Local-first, no API key required.
        </p>
      </Section>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-3xl px-6 text-center text-sm text-muted">
        <div className="border-t border-border pt-8">
          <a href={REPO} className="text-white/90 hover:text-white">
            github.com/Mrbaeksang/deepcloak
          </a>
          <p className="mt-3">
            MIT · Credits{" "}
            <a className="underline" href="https://github.com/LearningCircuit/local-deep-research">
              local-deep-research
            </a>{" "}
            +{" "}
            <a className="underline" href="https://github.com/CloakHQ/CloakBrowser">
              CloakBrowser
            </a>
          </p>
          <p className="mt-3 text-xs text-muted/70">
            You are responsible for having the right to access whatever you fetch.
          </p>
        </div>
      </footer>
    </main>
  );
}
