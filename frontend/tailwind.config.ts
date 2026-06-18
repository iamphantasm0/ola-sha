import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14110D",
        panel: "#1E1A13",
        edge: "#2E2820",
        gold: "#C9A24B",
        "gold-soft": "rgba(201,162,75,0.12)",
        paper: "#F3EEE3",
        "paper-ink": "#2A241B",
        "paper-muted": "#857A66",
        text: "#EDE7DB",
        muted: "#9A8F7C",
        success: "#6FA06B",
        danger: "#B5654A",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        paper: "0 1px 0 rgba(255,255,255,0.5) inset, 0 18px 40px -24px rgba(0,0,0,0.7)",
      },
      keyframes: {
        stampIn: {
          "0%": { opacity: "0", transform: "scale(1.6) rotate(-18deg)" },
          "60%": { opacity: "1", transform: "scale(0.92) rotate(-10deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(-12deg)" },
        },
        riseIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        stampIn: "stampIn 0.5s cubic-bezier(0.2,0.8,0.2,1) both",
        riseIn: "riseIn 0.4s ease both",
      },
    },
  },
  plugins: [],
};

export default config;
