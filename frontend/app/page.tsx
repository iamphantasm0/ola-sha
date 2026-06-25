"use client";

import { ChatWindow } from "@/components/Chat/ChatWindow";
import { InputBar } from "@/components/Chat/InputBar";
import { StatusPanel } from "@/components/Sidebar/StatusPanel";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  const { messages, order, loading, send, newChat } = useChat();

  return (
    <main className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-line bg-panel px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold tracking-tight text-mint">Ola</span>
          <span className="hidden text-xs text-muted sm:inline">
            AI crypto ↔ fiat · by Vela Labs
          </span>
        </div>
        <button
          onClick={newChat}
          className="rounded-lg border border-line px-3 py-1.5 text-xs text-gray-200 hover:border-mint"
        >
          New chat
        </button>
      </header>

      <div className="flex min-h-0 flex-1">
        <section className="flex min-w-0 flex-1 flex-col">
          <ChatWindow messages={messages} loading={loading} />
          <InputBar onSend={send} disabled={loading} />
        </section>

        <aside className="hidden w-[280px] shrink-0 overflow-y-auto border-l border-line bg-panel md:block">
          <div className="border-b border-line px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted">
            Transaction
          </div>
          <StatusPanel order={order} />
        </aside>
      </div>
    </main>
  );
}
