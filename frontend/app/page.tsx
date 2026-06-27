"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthModal } from "../components/Auth/AuthModal";
import { ChatWindow } from "../components/Chat/ChatWindow";
import { OgRegistryStats } from "../components/OgRegistryStats";
import { HistoryPanel } from "../components/Sidebar/HistoryPanel";
import { SidebarPanel } from "../components/Sidebar/SidebarPanel";
import { useAuth } from "../hooks/useAuth";
import { useChat } from "../hooks/useChat";

export default function Home() {
  const { messages, order, actions, loading, send, runAction, newChat } = useChat();
  const { email, isAuthed, login, register, logout } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [showMobileHistory, setShowMobileHistory] = useState(false);

  return (
    <main className="ola-bg flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-edge px-5 py-3.5">
        <div className="flex items-baseline gap-3">
          <span className="font-display text-2xl font-semibold tracking-tight text-gold">Ola</span>
          <span className="hidden text-[11px] uppercase tracking-[0.22em] text-muted sm:inline">
            stablecoin concierge
          </span>
        </div>
        <div className="flex items-center gap-2.5">
          <Link
            href="/verify"
            className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted transition-colors hover:border-gold/50 hover:text-text"
          >
            Verify on 0G
          </Link>
          <button
            onClick={newChat}
            className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted transition-colors hover:border-gold/50 hover:text-text"
          >
            New transaction
          </button>
          {isAuthed ? (
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={() => setShowMobileHistory(true)}
                className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted transition-colors hover:border-gold/50 hover:text-text md:hidden"
              >
                History
              </button>
              <span className="hidden font-mono text-xs text-muted sm:inline">{email}</span>
              <button
                onClick={logout}
                className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted transition-colors hover:border-gold/50 hover:text-text"
              >
                Sign out
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAuth(true)}
              className="rounded-full bg-gold px-4 py-1.5 text-xs font-medium text-ink transition-transform hover:-translate-y-px"
            >
              Sign in
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <ChatWindow
            messages={messages}
            actions={actions}
            authed={isAuthed}
            loading={loading}
            settledOrder={order?.status === "SETTLED" ? order : null}
            onSend={send}
            onRun={runAction}
            onRequireLogin={() => setShowAuth(true)}
          />
        </div>
        <aside className="hidden w-[300px] shrink-0 flex-col gap-3 p-3 md:flex">
          <div className="min-h-0 flex-1">
            <SidebarPanel order={order} authed={isAuthed} userKey={email} />
          </div>
          <OgRegistryStats variant="compact" />
        </aside>
      </div>

      {showAuth && (
        <AuthModal onClose={() => setShowAuth(false)} onLogin={login} onRegister={register} />
      )}

      {showMobileHistory && isAuthed && (
        <div className="ola-bg fixed inset-0 z-50 flex flex-col md:hidden">
          <header className="flex items-center justify-between border-b border-edge px-4 py-3">
            <span className="font-display text-lg text-gold">Your ramps</span>
            <button
              type="button"
              onClick={() => setShowMobileHistory(false)}
              className="rounded-full border border-edge px-3 py-1.5 text-xs text-muted"
            >
              Close
            </button>
          </header>
          <div className="flex-1 overflow-hidden p-3">
            <HistoryPanel refreshKey={email ?? undefined} />
          </div>
        </div>
      )}
    </main>
  );
}
