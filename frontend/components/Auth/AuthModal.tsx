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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-sm rounded-2xl border border-edge bg-panel p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold text-accent">
            {mode === "login" ? "Log in" : "Create account"}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
            ✕
          </button>
        </div>

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-2 w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <input
          type="password"
          placeholder="Password (min 6 chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          className="mb-3 w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        />

        {error && <div className="mb-3 text-xs text-red-400">{error}</div>}

        <button
          onClick={submit}
          disabled={busy || !email || !password}
          className="w-full rounded-lg bg-accent py-2 text-sm font-medium text-ink disabled:opacity-40"
        >
          {busy ? "…" : mode === "login" ? "Log in" : "Sign up"}
        </button>

        <button
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError(null);
          }}
          className="mt-3 w-full text-center text-xs text-gray-400 hover:text-gray-200"
        >
          {mode === "login" ? "No account? Sign up" : "Have an account? Log in"}
        </button>
      </div>
    </div>
  );
}
