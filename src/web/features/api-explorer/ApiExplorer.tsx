import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { AppShell } from "../../components/AppShell";
import { Card } from "../../components/Card";
import { Button } from "../../components/Button";
import { LoadingState } from "../../components/LoadingState";
import { ErrorState } from "../../components/ErrorState";
import {
  operations,
  prepareRequest,
  requestSchema,
  responseText,
  type Document,
  type Entry,
  type SeedExample,
} from "./contract";
import exampleJSON from "./examples.json?raw";
import "./explorer.css";

const examples = JSON.parse(exampleJSON) as SeedExample[];

export default function ApiExplorer() {
  const [document, setDocument] = useState<Document | null>(null);
  const [loadError, setLoadError] = useState("");
  const [retry, setRetry] = useState(0);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState("");
  const [values, setValues] = useState<Record<string, string>>({});
  const [body, setBody] = useState("");
  const [auth, setAuth] = useState<"session" | "bearer">("session");
  const [token, setToken] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{
    status: number;
    contentType: string;
    text: string;
  } | null>(null);
  const [sending, setSending] = useState(false);
  const activeRequest = useRef<AbortController | null>(null);
  const generation = useRef(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoadError("");
    fetch("/api/v1/schema/?format=json", {
      credentials: "omit",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok)
          throw new Error(`Schema request failed (${response.status}).`);
        const data = (await response.json()) as Document;
        operations(data);
        if (!controller.signal.aborted) setDocument(data);
      })
      .catch((cause: Error) => {
        if (!controller.signal.aborted) setLoadError(cause.message);
      });
    return () => controller.abort();
  }, [retry]);

  useEffect(
    () => () => {
      activeRequest.current?.abort();
      ++generation.current;
    },
    [],
  );
  const entries = useMemo(
    () => (document ? operations(document) : []),
    [document],
  );
  const entry = entries.find((item) => item.key === selected);
  const matches = entries.filter((item) =>
    `${item.method} ${item.path} ${item.summary ?? ""}`
      .toLowerCase()
      .includes(filter.toLowerCase()),
  );
  const writes = entry && !["get", "head", "options"].includes(entry.method);

  function choose(item: Entry, seed?: SeedExample) {
    activeRequest.current?.abort();
    ++generation.current;
    setSending(false);
    setSelected(item.key);
    setValues({});
    setBody(seed?.body ? JSON.stringify(seed.body, null, 2) : "");
    setConfirmed(false);
    setError("");
    setResult(null);
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    if (!entry || sending) return;
    setError("");
    setResult(null);
    const version = ++generation.current;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    try {
      if (writes && !confirmed)
        throw new Error("Confirm this write request before sending.");
      const request = prepareRequest(entry, values, body, auth, token);
      const controller = new AbortController();
      activeRequest.current = controller;
      timeout = setTimeout(() => controller.abort(), 30_000);
      setSending(true);
      const response = await fetch(request.url, {
        ...request.init,
        signal: controller.signal,
      });
      const text = await responseText(response);
      if (version === generation.current)
        setResult({
          status: response.status,
          contentType: response.headers.get("Content-Type") ?? "",
          text,
        });
    } catch (cause) {
      if (version === generation.current) setError((cause as Error).message);
    } finally {
      clearTimeout(timeout);
      if (version === generation.current) {
        setSending(false);
        setConfirmed(false);
      }
    }
  }

  return (
    <AppShell nav={<a href="/">Back to Conflux</a>}>
      <div className="cx-api-explorer">
        <Card title="API explorer" as="h2">
          <p>
            Browse this server's API and send requests using your current
            session or a scoped bearer token.
          </p>
          {loadError ? (
            <ErrorState
              message={loadError}
              onRetry={() => setRetry((count) => count + 1)}
            />
          ) : !document ? (
            <LoadingState label="Loading API schema…" />
          ) : (
            <>
              <fieldset disabled={sending}>
                <legend>Built-in examples</legend>
                {examples.map((seed) => {
                  const item = entries.find(
                    (row) => row.key === `${seed.method} ${seed.path}`,
                  );
                  return (
                    item && (
                      <Button
                        key={seed.label}
                        variant="secondary"
                        onClick={() => {
                          setFilter("");
                          choose(item, seed);
                        }}
                      >
                        {seed.label}
                      </Button>
                    )
                  );
                })}
              </fieldset>
              <label>
                Search operations
                <input
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                />
              </label>
              <label>
                Operation
                <select
                  value={selected}
                  disabled={sending}
                  onChange={(event) => {
                    const item = entries.find(
                      (row) => row.key === event.target.value,
                    );
                    if (item) choose(item);
                  }}
                >
                  <option value="">Choose an operation</option>
                  {entry && !matches.includes(entry) && (
                    <option value={entry.key}>
                      {entry.method.toUpperCase()} {entry.path}
                    </option>
                  )}
                  {matches.map((item) => (
                    <option key={item.key} value={item.key}>
                      {item.method.toUpperCase()} {item.path}
                    </option>
                  ))}
                </select>
              </label>
              <p>
                {matches.length} matching operations.{" "}
                <a href="/api/v1/schema/">Download schema</a>
              </p>
              {entry && (
                <>
                  <h3>
                    {entry.method.toUpperCase()} {entry.path}
                  </h3>
                  {entry.summary && <p>{entry.summary}</p>}
                  {entry.description && <p>{entry.description}</p>}
                  <form onSubmit={send}>
                    <fieldset disabled={sending}>
                      <legend>Request</legend>
                      {(entry.parameters ?? []).map((parameter) => {
                        const key = `${parameter.in}:${parameter.name}`;
                        return (
                          <label key={key}>
                            {parameter.name} ({parameter.in}
                            {parameter.required ? ", required" : ""})
                            <input
                              value={values[key] ?? ""}
                              onChange={(event) => {
                                setValues((current) => ({
                                  ...current,
                                  [key]: event.target.value,
                                }));
                                setConfirmed(false);
                              }}
                              required={parameter.required}
                            />
                            {parameter.description && (
                              <small>{parameter.description}</small>
                            )}
                            {parameter.schema?.type === "array" && (
                              <small>Enter a JSON array.</small>
                            )}
                          </label>
                        );
                      })}
                      {entry.requestBody && (
                        <label>
                          JSON request body
                          <textarea
                            rows={9}
                            value={body}
                            onChange={(event) => {
                              setBody(event.target.value);
                              setConfirmed(false);
                            }}
                            spellCheck={false}
                          />
                        </label>
                      )}
                      <label>
                        Authentication
                        <select
                          value={auth}
                          onChange={(event) => {
                            setAuth(event.target.value as "session" | "bearer");
                            setToken("");
                            setConfirmed(false);
                          }}
                        >
                          <option value="session">
                            Current session cookie
                          </option>
                          <option value="bearer">Scoped bearer token</option>
                        </select>
                      </label>
                      {auth === "bearer" && (
                        <label>
                          Bearer token
                          <input
                            type="password"
                            autoComplete="off"
                            value={token}
                            onChange={(event) => setToken(event.target.value)}
                            required
                          />
                        </label>
                      )}
                      <p>
                        Credentials stay in page memory. Bearer mode sends no
                        session cookie. Some operations require a human session.
                      </p>
                      {writes && (
                        <label>
                          <input
                            type="checkbox"
                            checked={confirmed}
                            onChange={(event) =>
                              setConfirmed(event.target.checked)
                            }
                          />
                          I intend to send this {entry.method.toUpperCase()}{" "}
                          request and change server data.
                        </label>
                      )}
                      <Button
                        type="submit"
                        disabled={sending || (!!writes && !confirmed)}
                      >
                        {sending ? "Sending…" : "Send request"}
                      </Button>
                    </fieldset>
                  </form>
                  <details>
                    <summary>Request schema and authentication</summary>
                    <pre>
                      {JSON.stringify(
                        {
                          body: requestSchema(entry, document),
                          parameters: entry.parameters,
                          security: entry.security,
                        },
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                  <details>
                    <summary>Response contract</summary>
                    <pre>{JSON.stringify(entry.responses, null, 2)}</pre>
                  </details>
                </>
              )}
              {error && <p role="alert">{error}</p>}
              {result && (
                <section aria-label="API response">
                  <h3>HTTP {result.status}</h3>
                  <p>{result.contentType}</p>
                  <pre>{result.text}</pre>
                </section>
              )}
            </>
          )}
        </Card>
      </div>
    </AppShell>
  );
}
