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
    title: "DeepCloak — deep research that reads bot-walled pages",
    description: "Deep research that reads pages other tools can't — even behind a Bot Wall.",
    type: "website",
    url: "https://deepcloak.vercel.app",
    siteName: "DeepCloak",
    images: [{ url: "/og.png", width: 1280, height: 640, alt: "DeepCloak bypassing Cloudflare/Turnstile in a real run" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "DeepCloak — deep research that reads bot-walled pages",
    description: "Deep research that reads pages other tools can't — even behind a Bot Wall.",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jbmono.variable}`}>
      <body className="stars font-sans antialiased">{children}</body>
    </html>
  );
}
