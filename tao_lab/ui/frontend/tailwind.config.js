/** @type {import('tailwindcss').Config} */
// Tokens kept in sync with tao_lab/ui/theme.py and static/style.css.
export default {
  content: ["./*.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        indigo: {
          deep: "#1E3A5F",
          ink: "#0F172A",
        },
        slate: {
          DEFAULT: "#475569",
          soft: "#94A3B8",
        },
        tangerine: {
          DEFAULT: "#F97316",
          soft: "#FFF7ED",
        },
        mist: "#F8FAFC",
        cloud: "#FFFFFF",
        hairline: "#E2E8F0",
        success: "#059669",
        warning: "#D97706",
        danger: "#DC2626",
      },
      borderRadius: {
        card: "12px",
        control: "8px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(15, 23, 42, 0.04)",
        lifted: "0 4px 12px rgba(15, 23, 42, 0.06)",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "Inter",
          "Söhne",
          "system-ui",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SF Mono", "Menlo", "monospace"],
      },
      letterSpacing: {
        tightish: "-0.01em",
      },
    },
  },
  plugins: [],
};
