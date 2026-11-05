import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        sosp: {
          blue: {
            100: "var(--sosp-blue-100)",
            500: "var(--sosp-blue-500)",
            700: "var(--sosp-blue-700)",
          },
          yellow: {
            500: "var(--sosp-yellow-500)",
            700: "var(--sosp-yellow-700)",
          },
          green: {
            500: "var(--sosp-green-500)",
          },
          red: {
            500: "var(--sosp-red-500)",
          },
          gray: {
            100: "var(--sosp-gray-100)",
            300: "var(--sosp-gray-300)",
            500: "var(--sosp-gray-500)",
            700: "var(--sosp-gray-700)",
            900: "var(--sosp-gray-900)",
          },
        },
      },
      fontFamily: {
        sans: ["Public Sans", "var(--font-public-sans)", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
      maxWidth: {
        sosp: "1200px",
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "16px",
      },
      boxShadow: {
        sm: "0 1px 2px rgba(16, 24, 40, 0.06)",
        md: "0 4px 8px rgba(16, 24, 40, 0.08)",
        lg: "0 12px 24px rgba(16, 24, 40, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;

