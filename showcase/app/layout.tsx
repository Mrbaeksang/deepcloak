import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DeepCloak — deep research that reads bot-walled pages",
  description:
    "A local-first deep research agent that bypasses Cloudflare, Datadome, Turnstile & reCAPTCHA to read the whole web.",
  openGraph: {
    title: "DeepCloak",
    description: "Deep research that reads pages other tools can't — even behind a Bot Wall.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-mono antialiased">{children}</body>
    </html>
  );
}
