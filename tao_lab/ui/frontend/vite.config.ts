import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Streamlit custom components are loaded as static HTML inside an iframe.
// We bundle each component as a self-contained ES module + CSS, served from
// `dist/` and registered in Python via `components.declare_component(path=…)`.
// Multi-page mode: one HTML entry per component, all sharing the same React
// runtime + Tailwind build for cache locality.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: false,
    rollupOptions: {
      input: {
        stepper: "stepper.html",
        verdict: "verdict.html",
        prescription: "prescription.html",
      },
    },
  },
  server: {
    port: 5173,
  },
});
