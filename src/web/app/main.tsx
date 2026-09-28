import { lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "../styles/main.css";

const ApiExplorer = lazy(() => import("../features/api-explorer/ApiExplorer"));
const explorer =
  new URLSearchParams(window.location.search).get("api") === "explorer";

createRoot(document.getElementById("root")!).render(
  explorer ? (
    <Suspense fallback={<p>Loading API explorer…</p>}>
      <ApiExplorer />
    </Suspense>
  ) : (
    <App />
  ),
);
