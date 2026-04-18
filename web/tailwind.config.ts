import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
    "./src/store/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#07111f",
        panel: "rgba(14, 22, 40, 0.78)",
        line: "rgba(157, 178, 255, 0.16)",
        accent: "#77d7ff",
        accent2: "#9986ff",
        mist: "#aebddf"
      },
      boxShadow: {
        glow: "0 12px 60px rgba(53, 112, 255, 0.18)",
        panel: "0 24px 60px rgba(0, 0, 0, 0.25)"
      },
      backgroundImage: {
        "hero-grid":
          "linear-gradient(rgba(154,169,207,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(154,169,207,0.08) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;
