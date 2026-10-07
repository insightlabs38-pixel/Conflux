import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/Button";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { ApiError } from "../../lib/api";
import { LIVE, previewAs, previewProblem } from "../../lib/previewContext";
import type { ThemeConfig } from "./ThemeSettings";

/** The three widths an organizer checks a public page at; the frame is really that wide, so the
 * page's own breakpoints apply (a narrower box would not trigger them). */
export const DEVICES = [
  { id: "desktop", label: "Desktop", width: 1440, height: 760 },
  { id: "tablet", label: "Tablet", width: 768, height: 900 },
  { id: "mobile", label: "Mobile", width: 390, height: 780 },
] as const;
type Device = (typeof DEVICES)[number];

/** How long to wait after the last change before asking the server, so dragging a slider is one
 * request, not fifty. */
export const PREVIEW_DELAY_MS = 350;

/**
 * The organizer's preview of the public page with the appearance as it is in the form, saved or
 * not (PREVIEW_CONTEXT surface `page`, PD-F004-B03-T07). The server renders the page with the real
 * template from the saved blocks and the drafted appearance; the browser only shows it in a frame
 * without scripts or storage, at the chosen width, scaled to fit. Nothing is saved or sent.
 */
export function PagePreview({
  workspaceId,
  eventId,
  theme,
  config,
}: {
  workspaceId: string;
  eventId: string;
  theme: string;
  config: ThemeConfig;
}) {
  const [device, setDevice] = useState<Device>(DEVICES[0]);
  const [html, setHtml] = useState("");
  const [problem, setProblem] = useState("");
  const [failed, setFailed] = useState("");
  const [busy, setBusy] = useState(false);
  const [room, setRoom] = useState(0);
  const frame = useRef<HTMLDivElement>(null);
  const body = JSON.stringify({ theme, config });

  useEffect(() => {
    const box = frame.current;
    if (!box) return;
    const measure = () => setRoom(box.clientWidth);
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const watcher = new ResizeObserver(measure);
    watcher.observe(box);
    return () => watcher.disconnect();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setBusy(true);
      const draft = JSON.parse(body) as { theme: string; config: ThemeConfig };
      const cleaned = Object.fromEntries(
        Object.entries(draft.config).filter(([, value]) => value !== ""),
      );
      previewAs<{ html: string }>(
        workspaceId,
        "page",
        { event: eventId },
        LIVE,
        controller.signal,
        { theme: draft.theme, theme_config: cleaned },
      )
        .then((answer) => {
          setHtml(answer.data.html);
          setProblem("");
          setFailed("");
        })
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          if (error instanceof ApiError && error.status === 400)
            setProblem(previewProblem(error));
          else setFailed(previewProblem(error));
        })
        .finally(() => {
          if (!controller.signal.aborted) setBusy(false);
        });
    }, PREVIEW_DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [workspaceId, eventId, body]);

  const scale = room > 0 ? Math.min(1, room / device.width) : 1;
  return (
    <section className="cx-page-preview" aria-label="Public page preview">
      <div className="cx-page-preview__bar">
        <h3>Preview</h3>
        <div role="group" aria-label="Preview width">
          {DEVICES.map((item) => (
            <Button
              key={item.id}
              variant="secondary"
              size="sm"
              type="button"
              aria-pressed={item.id === device.id}
              onClick={() => setDevice(item)}
            >
              {item.label} {item.width}px
            </Button>
          ))}
        </div>
      </div>
      <p className="cx-muted">
        The saved page blocks with the appearance as it is in this form. Nothing
        is saved or sent.
      </p>
      {problem && (
        <ErrorState
          message={`The preview cannot be drawn yet: ${problem}`}
          kept="Your changes are still in the form and nothing was saved; the preview updates when this is fixed."
        />
      )}
      {failed && (
        <ErrorState
          kind="read"
          message={failed}
          onRetry={() => setDevice({ ...device })}
        />
      )}
      {!html && !problem && !failed && (
        <LoadingState label="Drawing the page…" />
      )}
      <div
        ref={frame}
        className="cx-page-preview__stage"
        aria-busy={busy || undefined}
        style={{ height: html ? device.height * scale : undefined }}
      >
        {html && (
          <iframe
            key={device.id}
            title={`Public page preview, ${device.label.toLowerCase()} ${device.width}px wide`}
            sandbox=""
            srcDoc={html}
            width={device.width}
            height={device.height}
            style={{ transform: `scale(${scale})` }}
            data-device={device.id}
          />
        )}
      </div>
    </section>
  );
}
