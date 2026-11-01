/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: "#F4EFE6",
          secondary: "#EBE4D8",
          muted: "#E2DACB",
          border: "#D8CEBC",
        },
        ink: {
          DEFAULT: "#08161B",
          muted: "#3D4F55",
          faint: "#6A7E85",
        },
        cyanotype: {
          DEFAULT: "#1C354D",
          deep: "#0D1C29",
          border: "#284A6B",
        },
        halftone: {
          teal: "#1D5B6B",
        },
        cobalt: "#2E6DA4",
        cerulean: "#5894C4",
        meadow: "#4A6B32",
        moss: "#233818",
        terracotta: "#C87D55",
        "cloud-chalk": "#EAE7DC",
      },
      fontFamily: {
        serif: ["Newsreader", "Instrument Serif", "Georgia", "serif"],
        sans: ["Geist", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Geist Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        paper: "0 1px 3px rgba(8, 22, 27, 0.05), 0 1px 2px rgba(8, 22, 27, 0.03)",
        editorial: "0 4px 20px -2px rgba(8, 22, 27, 0.08), 0 2px 6px -1px rgba(8, 22, 27, 0.04)",
        cyanotype: "0 8px 30px rgba(13, 28, 41, 0.35)",
      },
    },
  },
  plugins: [],
};
