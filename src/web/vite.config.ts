import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server only (unused by `vite build`): proxies API calls to the Django
// app so the same relative `/api/v1/...` paths used in production also work
// against `pnpm dev`. Override for the containerized dev service, which
// reaches the app by its Compose service name instead of localhost.
export default defineConfig({
  plugins: [react()],
  // The post-spec plan uses `src/web/public/**` for source (event-site,
  // project-gallery, project-page), not Vite's copy-verbatim static dir.
  // No static assets are served today, so free the path instead of aliasing.
  publicDir: false,
  server: {
    host: true,
    proxy: {
      "/api": process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8080",
    },
  },
});
