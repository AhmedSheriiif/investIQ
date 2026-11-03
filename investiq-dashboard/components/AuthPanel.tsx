"use client";

import { useState } from "react";
import { User } from "@supabase/supabase-js";

export function AuthPanel({
  user,
  onSignIn,
  onSignUp,
  onSignOut,
  labels,
}: {
  user: User | null;
  onSignIn: (email: string, password: string) => Promise<void>;
  onSignUp: (email: string, password: string) => Promise<void>;
  onSignOut: () => Promise<void>;
  labels: {
    signIn: string;
    signUp: string;
    signOut: string;
    email: string;
    password: string;
    createAccount: string;
    alreadyHaveAccount: string;
    checkEmailToConfirm: string;
  };
}) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "signup") {
        await onSignUp(email, password);
        setConfirmMessage(true);
      } else {
        await onSignIn(email, password);
        setOpen(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  if (user) {
    return (
      <div className="flex items-center gap-3 text-xs font-mono">
        <span className="text-muted">{user.email}</span>
        <button
          onClick={onSignOut}
          className="text-muted-dim hover:text-signal-amber transition-colors"
        >
          {labels.signOut}
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="px-3 py-1.5 rounded-md border border-hairline bg-panel text-xs font-mono
                   text-muted hover:text-ink hover:border-signal-amber/40 transition-colors"
      >
        {labels.signIn}
      </button>

      {open && (
        <div className="absolute end-0 mt-2 w-72 bg-panel border border-hairline rounded-lg p-4 shadow-xl z-10">
          {confirmMessage ? (
            <p className="text-sm text-signal-green">{labels.checkEmailToConfirm}</p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={labels.email}
                required
                className="w-full bg-panel-raised border border-hairline rounded-md px-3 py-2 text-sm
                           text-ink placeholder:text-muted-dim outline-none focus:border-signal-amber/60"
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={labels.password}
                required
                minLength={6}
                className="w-full bg-panel-raised border border-hairline rounded-md px-3 py-2 text-sm
                           text-ink placeholder:text-muted-dim outline-none focus:border-signal-amber/60"
              />
              {error && <p className="text-xs text-signal-amber">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-4 py-2 rounded-md bg-panel-raised border border-hairline text-sm
                           text-ink hover:border-signal-amber/50 hover:text-signal-amber transition-colors
                           disabled:opacity-40"
              >
                {mode === "signup" ? labels.createAccount : labels.signIn}
              </button>
              <button
                type="button"
                onClick={() => setMode(mode === "signup" ? "signin" : "signup")}
                className="w-full text-xs text-muted-dim hover:text-muted transition-colors"
              >
                {mode === "signup" ? labels.alreadyHaveAccount : labels.signUp}
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
