"use client";

import { useState } from "react";
import { AuthModal } from "../components/Auth/AuthModal";
import { ChatWindow } from "../components/Chat/ChatWindow";
import { StatusPanel } from "../components/Sidebar/StatusPanel";
import { useAuth } from "../hooks/useAuth";
import { useChat } from "../hooks/useChat";

export default function Home() {
  const { messages, order, actions, loading, send, runAction, newChat } = useChat();
  const { email, isAuthed, login, register, logout } = useAuth();
  const [showAuth, setShowAuth] = useState(false);

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
          <button
            onClick={newChat}
            className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted transition-colors hover:border-gold/50 hover:text-text"
          >
            New transaction
          </button>
          {isAuthed ? (
            <div className="flex items-center gap-2.5">
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
            onSend={send}
            onRun={runAction}
            onRequireLogin={() => setShowAuth(true)}
          />
        </div>
        <aside className="hidden w-[300px] shrink-0 p-3 md:block">
          <StatusPanel order={order} />
        </aside>
      </div>

      {showAuth && (
        <AuthModal onClose={() => setShowAuth(false)} onLogin={login} onRegister={register} />
      )}
    </main>
  );
}
