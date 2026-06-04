"use client";

import { motion } from "framer-motion";
import evidence from "../data/evidence.json";

const REPO = "https://github.com/Mrbaeksang/deepcloak";

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

function Section({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className={`mx-auto w-full max-w-3xl px-6 ${className}`}
    >
      {children}
    </motion.section>
  );
}

export default function Page() {
  return (
    <main className="flex flex-col items-center gap-28 py-24">
      {/* Hero */}
      <Section className="text-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.7 }}
          className="text-6xl"
        >
          🛡️
        </motion.div>
        <h1 className="mt-4 text-5xl font-bold tracking-tight sm:text-6xl">DeepCloak</h1>
        <p className="mx-auto mt-5 max-w-xl text-lg text-zinc-300">
          Deep research that reads the <span className="text-cyber">whole</span> web — even pages
          behind <span className="text-cloak">Cloudflare, Datadome, Turnstile &amp; reCAPTCHA</span>.
        </p>
        <div className="mt-8 flex items-center justify-center gap-4">
          <a
            href={REPO}
            className="rounded-lg bg-cloak px-5 py-3 font-semibold text-white transition hover:opacity-90"
          >
            ★ Star on GitHub
          </a>
          <a
            href="#evidence"
            className="rounded-lg border border-zinc-700 px-5 py-3 font-semibold text-zinc-200 transition hover:border-zinc-500"
          >
            See the evidence ↓
          </a>
        </div>
        <p className="mt-6 text-sm text-zinc-500">pip install deepcloak · MIT · CLI · MCP · Claude skill</p>
      </Section>

      {/* Live bypass demo */}
      <Section className="text-center">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-cyber">Live capture</h2>
        <p className="mt-2 text-2xl font-bold">Watch it walk through a Cloudflare Turnstile</p>
        <div className="mt-8 overflow-hidden rounded-xl border border-zinc-800 bg-black/40 shadow-2xl">
          <div className="flex items-center gap-1.5 border-b border-zinc-800 bg-zinc-900/70 px-4 py-2.5">
            <span className="h-3 w-3 rounded-full bg-red-500/80" />
            <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
            <span className="h-3 w-3 rounded-full bg-green-500/80" />
            <span className="ml-3 text-xs text-zinc-500">nowsecure.nl — stealth fetch</span>
          </div>
          <video
            className="w-full"
            src="/bypass.mp4"
            poster="/bypassed.png"
            autoPlay
            muted
            loop
            playsInline
          />
        </div>
        <p className="mt-3 text-sm text-zinc-500">
          Real headless capture (cloakbrowser). The page resolves the Turnstile challenge and the
          content loads — no human in the loop.
        </p>
      </Section>

      {/* Bypass counter */}
      <Section className="text-center">
        <div className="grid grid-cols-3 gap-4">
          {[
            { n: summary.bypassed, label: "Bot Walls bypassed" },
            { n: summary.total, label: "sources fetched" },
            { n: `${Math.round((records.find((r) => r.bypassed)?.elapsed_ms ?? 0) / 100) / 10}s`, label: "to bypass Turnstile" },
          ].map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.8 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6"
            >
              <div className="text-4xl font-bold text-cyber">{s.n}</div>
              <div className="mt-1 text-xs text-zinc-400">{s.label}</div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* Evidence timeline */}
      <Section className="" >
        <div id="evidence" className="-mt-24 pt-24" />
        <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-cyber">
          Evidence Record
        </h2>
        <p className="mt-2 text-center text-2xl font-bold">Every fetch, on the record</p>
        <p className="mx-auto mt-2 max-w-lg text-center text-sm text-zinc-400">
          Plain fetch first; escalate to a stealth Bypass only when a Bot Wall is detected. Open
          pages stay fast.
        </p>
        <div className="mt-10 flex flex-col gap-4">
          {records.map((r, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className={`rounded-xl border p-5 ${
                r.bypassed ? "border-cloak/50 bg-cloak/10" : "border-zinc-800 bg-zinc-900/40"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="truncate font-semibold">{r.url}</span>
                <span className="shrink-0 text-xs text-zinc-500">{r.elapsed_ms} ms</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                <span className="rounded bg-zinc-800 px-2 py-0.5 text-zinc-300">
                  plain → {r.plain_status ?? "—"}
                </span>
                {r.bot_wall && r.bot_wall !== "forced" ? (
                  <>
                    <span className="text-zinc-600">→</span>
                    <span className="rounded bg-red-500/20 px-2 py-0.5 text-red-300">
                      🧱 {r.bot_wall}
                    </span>
                  </>
                ) : null}
                {r.escalated ? (
                  <>
                    <span className="text-zinc-600">→</span>
                    <span className="rounded bg-cyber/20 px-2 py-0.5 text-cyber">⚡ escalate</span>
                  </>
                ) : null}
                <span className="text-zinc-600">→</span>
                {r.bypassed ? (
                  <span className="rounded bg-green-500/20 px-2 py-0.5 text-green-300">
                    ✅ bypassed
                  </span>
                ) : (
                  <span className="rounded bg-green-500/10 px-2 py-0.5 text-green-200/80">
                    ✓ open page
                  </span>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </Section>

      {/* How it works */}
      <Section className="text-center">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-cyber">How it works</h2>
        <div className="mt-8 flex flex-col items-stretch gap-3 text-left sm:flex-row sm:items-center sm:justify-center">
          {["🔎 search (DuckDuckGo)", "🌐 plain fetch", "🧱 Bot Wall?", "⚡ Stealth Fetch", "📄 cited report"].map(
            (step, i, arr) => (
              <div key={i} className="flex items-center gap-3">
                <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3 text-sm">
                  {step}
                </div>
                {i < arr.length - 1 ? <span className="hidden text-cloak sm:inline">→</span> : null}
              </div>
            )
          )}
        </div>
        <p className="mx-auto mt-6 max-w-lg text-sm text-zinc-400">
          Built on <span className="text-zinc-200">local-deep-research</span> (the research loop) and{" "}
          <span className="text-zinc-200">CloakBrowser</span> (the stealth browser). Local-first, no
          API key required.
        </p>
      </Section>

      {/* Footer */}
      <footer className="mt-8 w-full max-w-3xl px-6 text-center text-sm text-zinc-500">
        <div className="border-t border-zinc-800 pt-8">
          <a href={REPO} className="text-zinc-300 hover:text-white">
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
          <p className="mt-3 text-xs text-zinc-600">
            You are responsible for having the right to access whatever you fetch.
          </p>
        </div>
      </footer>
    </main>
  );
}
