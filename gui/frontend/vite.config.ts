import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run dev` serves the front end with hot reload; API calls go to the
// Python server started with `python -m sweetpea_gui`.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
});
