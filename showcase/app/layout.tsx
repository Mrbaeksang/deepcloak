import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const jbmono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jbmono", display: "swap" });

export const metadata: Metadata = {
  title: "DeepCloak — research with explicit fetch decisions and evidence",
  description:
    "A local-first research tool with explicit fetch decisions, source evidence, and cited reports. CLI and MCP.",
  metadataBase: new URL("https://deepcloak.vercel.app"),
  alternates: { canonical: "/" },
  openGraph: {
    title: "DeepCloak — research with explicit fetch decisions and evidence",
    description: "Local-first research with explicit fetch decisions, source evidence, and cited reports.",
    type: "website",
    url: "https://deepcloak.vercel.app",
    siteName: "DeepCloak",
    images: [{ url: "/og.png", width: 1280, height: 640, alt: "A recorded DeepCloak run" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "DeepCloak — research with explicit fetch decisions and evidence",
    description: "Local-first research with explicit fetch decisions, source evidence, and cited reports.",
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
