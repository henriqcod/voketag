import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        institutional: {
          bg: "#0f172a",
          card: "#1e293b",
          border: "#334155",
          muted: "#94a3b8",
          fg: "#f8fafc",
        },
        brand: {
          500: "#465fff",
          600: "#3641f5",
        },
        success: { 50: "#ecfdf3", 100: "#d1fadf", 500: "#12b76a", 600: "#039855" },
        error: { 50: "#fef3f2", 100: "#fee4e2", 500: "#f04438", 600: "#d92d20" },
      },
      boxShadow: {
        "theme-xs": "0px 1px 2px 0px rgba(16, 24, 40, 0.05)",
        "theme-sm": "0px 1px 3px 0px rgba(16, 24, 40, 0.1), 0px 1px 2px 0px rgba(16, 24, 40, 0.06)",
        "theme-md": "0px 4px 8px -2px rgba(16, 24, 40, 0.1), 0px 2px 4px -2px rgba(16, 24, 40, 0.06)",
      },
    },
  },
  plugins: [],
};
export default config;
