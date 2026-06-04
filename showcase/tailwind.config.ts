import type { Config } from "tailwindcss";

// DeepCloak showcase — cosmic / deep-space system (Railway-inspired, our palette).
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // cosmic neutrals
        space: "#0b0b0f", // deep space — page background
        surface: "#13111c", // elevated dark surface
        slate2: "#33323e", // cosmic slate (cards)
        border: "#2a2933",
        borderlit: "#545260",
        muted: "#a1a0ab", // asteroid gray
        // brand
        cloak: "#853bce", // nebula purple — primary (the cloak)
        cyber: "#22d3ee", // cyan — "bypassed" success accent
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jbmono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 80px -20px rgba(133,59,206,0.55)",
      },
    },
  },
  plugins: [],
};

export default config;
