import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0a0b0e",
        panel: "#13151a",
        edge: "#23262e",
        accent: "#5eead4",
      },
    },
  },
  plugins: [],
};

export default config;
