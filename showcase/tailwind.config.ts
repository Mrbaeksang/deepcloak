import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        ink: "#0a0a0f",
        cloak: "#8A2BE2",
        cyber: "#22d3ee",
      },
    },
  },
  plugins: [],
};

export default config;
