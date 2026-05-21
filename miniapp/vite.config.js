import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const allowedHosts = true;

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts,
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts,
    headers: {
      "ngrok-skip-browser-warning": "true",
    },
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
