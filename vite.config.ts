import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// The FastAPI backend (app.py) runs on :8000 in local/prod.
// In local dev these endpoints are proxied so the React app can call
// them with relative paths. When the backend is unreachable (e.g. the
// v0 preview), the API layer falls back to representative sample data.
const API_TARGET = process.env.VITE_API_TARGET || "http://localhost:8000"
const proxy = Object.fromEntries(
  ["/today", "/scorecard_data", "/market_meter_data", "/refresh-pipeline"].map((p) => [
    p,
    { target: API_TARGET, changeOrigin: true },
  ]),
)

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    proxy,
  },
})
