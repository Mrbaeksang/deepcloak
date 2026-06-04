import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const jbmono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jbmono", display: "swap" });

export const metadata: Metadata = {
  title: "DeepCloak — deep research that reads bot-walled pages",
  description:
    "A local-first deep research agent that bypasses Cloudflare, Datadome, Turnstile & reCAPTCHA to read the whole web.",
  metadataBase: new URL("https://deepcloak.vercel.app"),
  openGraph: {
    title: "DeepCloak",
    description: "Deep research that reads pages other tools can't — even behind a Bot Wall.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jbmono.variable}`}>
      <body className="stars font-sans antialiased">{children}</body>
    </html>
  );
}
