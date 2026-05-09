/** @type {import('tailwindcss').Config} */
// Tokens kept in sync with tao_lab/ui/theme.py and static/style.css.
export default {
  content: ["./*.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        indigo: {
          deep: "var(--tl-indigo-deep)",
          ink: "var(--tl-indigo-ink)",
        },
        slate: {
          DEFAULT: "var(--tl-slate)",
          soft: "var(--tl-slate-soft)",
        },
        tangerine: {
          DEFAULT: "var(--tl-tangerine)",
          soft: "var(--tl-tangerine-soft)",
        },
        mist: "var(--tl-mist)",
        cloud: "var(--tl-cloud)",
        hairline: "var(--tl-hairline)",
        success: "var(--tl-success)",
        warning: "var(--tl-warning)",
        danger: "var(--tl-danger)",
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
