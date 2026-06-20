/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The dev server proxies /api -> the backend so the browser talks to one origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  // Vitest = unit tests in src/ only. The Playwright e2e/ specs (also *.spec.ts)
  // are run by `npm run e2e`, not vitest — exclude them so vitest doesn't try
  // to collect a browser test.
  test: {
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx", "src/vite-env.d.ts", "src/**/*.test.{ts,tsx}", "src/test-setup.ts"],
      // A real gate, enforced by `npm test` (currently ~40% lines / 57% funcs /
      // 65% branches). Page components are primarily covered by the Playwright
      // e2e; raise these as you add more unit tests.
      thresholds: { statements: 38, branches: 55, functions: 50, lines: 38 },
    },
  },
});
