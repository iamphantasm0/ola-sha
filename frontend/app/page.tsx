"use client";

import { ChatWindow } from "../components/Chat/ChatWindow";
import { StatusPanel } from "../components/Sidebar/StatusPanel";
import { useChat } from "../hooks/useChat";

export default function Home() {
  const { messages, order, loading, send, newChat } = useChat();

  return (
    <main className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-edge px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-accent">Ola</span>
          <span className="text-xs text-gray-500">AI Crypto ↔ Fiat · powered by 0G</span>
        </div>
        <button
          onClick={newChat}
          className="rounded-lg border border-edge px-3 py-1.5 text-xs text-gray-300 hover:border-accent"
        >
          New Chat
        </button>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-hidden">
          <ChatWindow messages={messages} loading={loading} onSend={send} />
        </div>
        <aside className="hidden w-[260px] shrink-0 md:block">
          <StatusPanel order={order} />
        </aside>
      </div>
    </main>
  );
}
