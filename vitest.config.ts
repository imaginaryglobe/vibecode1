import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    include: ["challenge3/src/**/*.test.ts", "challenge3/src/**/*.test.tsx"],
  },
});
