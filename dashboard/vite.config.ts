import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Browser dev uses 5173; Tauri sets TAURI_DEV_PORT=1420 for the desktop app.
const port = Number(process.env.TAURI_DEV_PORT ?? 5173)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port,
    strictPort: true,
  },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_'],
})
