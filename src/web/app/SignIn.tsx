import { useEffect, useId, useState, type FormEvent } from "react";
import { Button } from "../components/Button";

type SsoConfig = {
  enabled: boolean;
  provider_name?: string;
  login_url?: string;
};

async function loadSso(): Promise<SsoConfig> {
  try {
    const response = await fetch("/api/v1/accounts/oidc/config/", {
      credentials: "include",
    });
    if (!response.ok) return { enabled: false };
    return (await response.json()) as SsoConfig;
  } catch {
    return { enabled: false };
  }
}

function failureMessage(status: number): string {
  if (status === 429) return "Too many failed attempts. Try again later.";
  if (status === 401) return "Invalid username or password.";
  return "Could not sign in. Try again.";
}

export function SignIn({ onSignedIn }: { onSignedIn: () => void }) {
  const ids = { user: useId(), password: useId() };
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const [sso, setSso] = useState<SsoConfig>({ enabled: false });

  useEffect(() => {
    let active = true;
    loadSso().then((config) => {
      if (active) setSso(config);
    });
    return () => {
      active = false;
    };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    try {
      const response = await fetch("/api/v1/accounts/login/", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        setError(failureMessage(response.status));
        setPassword("");
        return;
      }
      onSignedIn();
    } catch {
      setError("Could not reach the server. Check your connection and retry.");
    } finally {
      setPending(false);
    }
  }

  const next = encodeURIComponent(
    typeof window === "undefined"
      ? "/app/"
      : window.location.pathname + window.location.search,
  );

  return (
    <section aria-labelledby={`${ids.user}-title`} className="cx-signin">
      <h2 id={`${ids.user}-title`}>Sign in to see your workspaces.</h2>
      <form onSubmit={submit} noValidate={false}>
        <p>
          <label htmlFor={ids.user}>Username</label>
          <br />
          <input
            id={ids.user}
            name="username"
            autoComplete="username"
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </p>
        <p>
          <label htmlFor={ids.password}>Password</label>
          <br />
          <input
            id={ids.password}
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </p>
        {error && <p role="alert">{error}</p>}
        <Button type="submit" disabled={pending || !username || !password}>
          {pending ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      {sso.enabled && sso.login_url && (
        <p>
          <a href={`${sso.login_url}?next=${next}`}>
            Sign in with {sso.provider_name ?? "single sign-on"}
          </a>
        </p>
      )}
    </section>
  );
}
