import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  baseURL: 'http://localhost:5173',
  use: {
    headless: true,
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
  },
})
