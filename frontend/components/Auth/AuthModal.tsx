"use client";

import { useState } from "react";

export function AuthModal({
  onClose,
  onLogin,
  onRegister,
}: {
  onClose: () => void;
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (email: string, password: string) => Promise<void>;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") await onLogin(email.trim(), password);
      else await onRegister(email.trim(), password);
      onClose();
    } catch (e: any) {
      setError(e.message || "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  const inputCls =
    "mb-2.5 w-full rounded-lg border border-edge bg-ink px-3 py-2.5 text-sm text-text outline-none focus:border-gold/50 placeholder:text-muted/60";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div className="animate-riseIn w-full max-w-sm rounded-2xl border border-edge bg-panel p-6">
        <div className="mb-1 font-display text-xl text-gold">
          {mode === "login" ? "Welcome back" : "Open your concierge"}
        </div>
        <div className="mb-5 text-xs text-muted">
          {mode === "login"
            ? "Sign in to use your saved accounts."
            : "Save your bank and wallet for one-tap transactions."}
        </div>

        <input className={inputCls} type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input
          className={inputCls}
          type="password"
          placeholder="Password (min 6 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />

        {error && <div className="mb-3 text-xs text-danger">{error}</div>}

        <button
          onClick={submit}
          disabled={busy || !email || !password}
          className="w-full rounded-lg bg-gold py-2.5 text-sm font-medium text-ink transition-transform hover:-translate-y-px disabled:opacity-40 disabled:hover:translate-y-0"
        >
          {busy ? "…" : mode === "login" ? "Sign in" : "Create account"}
        </button>

        <div className="mt-4 flex items-center justify-between text-xs">
          <button
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
            className="text-muted hover:text-text"
          >
            {mode === "login" ? "New here? Create an account" : "Have an account? Sign in"}
          </button>
          <button onClick={onClose} className="text-muted hover:text-text">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
