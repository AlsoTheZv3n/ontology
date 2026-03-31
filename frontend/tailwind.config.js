/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#020617",
          container: "#0f172a",
          "container-high": "#1e293b",
          "container-highest": "#323538",
          bright: "#37393d",
        },
        "on-surface": {
          DEFAULT: "#f8fafc",
          variant: "#94a3b8",
        },
        primary: {
          DEFAULT: "#60a5fa",
          container: "#0066ff",
          "fixed-dim": "#3b82f6",
        },
        secondary: {
          DEFAULT: "#94a3b8",
          container: "#464747",
        },
        outline: {
          DEFAULT: "#334155",
          variant: "#424656",
        },
        inverse: {
          surface: "#e1e2e6",
          "on-surface": "#2e3134",
        },
      },
      fontFamily: {
        headline: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        label: ["Space Grotesk", "sans-serif"],
      },
      borderRadius: {
        sm: "2px",
        md: "4px",
        lg: "8px",
      },
    },
  },
  plugins: [],
};
