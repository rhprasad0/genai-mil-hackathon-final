/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  envPrefix: ['VITE_'],
  test: {
    environment: 'jsdom',
    setupFiles: ['src/test/setup.ts'],
    globals: true,
    exclude:
      process.env.VITEST_INCLUDE_SMOKE === '1'
        ? ['node_modules/**', 'dist/**', 'e2e/**']
        : ['node_modules/**', 'dist/**', 'e2e/**', 'tests/smoke/**'],
  },
})
