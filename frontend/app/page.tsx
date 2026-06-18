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
    <main className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-edge px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-accent">Ola</span>
          <span className="hidden text-xs text-gray-500 sm:inline">
            AI Crypto ↔ Fiat · powered by 0G
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={newChat}
            className="rounded-lg border border-edge px-3 py-1.5 text-xs text-gray-300 hover:border-accent"
          >
            New Chat
          </button>
          {isAuthed ? (
            <div className="flex items-center gap-2">
              <span className="hidden text-xs text-gray-400 sm:inline">{email}</span>
              <button
                onClick={logout}
                className="rounded-lg border border-edge px-3 py-1.5 text-xs text-gray-300 hover:border-accent"
              >
                Log out
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAuth(true)}
              className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-ink"
            >
              Log in / Sign up
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
        <aside className="hidden w-[260px] shrink-0 md:block">
          <StatusPanel order={order} />
        </aside>
      </div>

      {showAuth && (
        <AuthModal onClose={() => setShowAuth(false)} onLogin={login} onRegister={register} />
      )}
    </main>
  );
}
