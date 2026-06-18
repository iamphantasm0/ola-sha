"use client";

import { useEffect, useRef } from "react";
import { Action, ChatMessage } from "../../lib/types";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { ActionButtons } from "./ActionButtons";

export function ChatWindow({
  messages,
  actions,
  authed,
  loading,
  onSend,
  onRun,
  onRequireLogin,
}: {
  messages: ChatMessage[];
  actions: Action[];
  authed: boolean;
  loading: boolean;
  onSend: (text: string) => void;
  onRun: (action: string, payload?: Record<string, any>, userEcho?: string) => void;
  onRequireLogin: () => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, actions]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
        </div>
        {loading && (
          <div className="mt-3 flex justify-start">
            <div className="rounded-2xl rounded-bl-sm border border-edge bg-panel px-4 py-2.5 text-sm text-gray-400">
              Ola is typing…
            </div>
          </div>
        )}
        {!loading && (
          <ActionButtons
            actions={actions}
            authed={authed}
            disabled={loading}
            onRun={onRun}
            onRequireLogin={onRequireLogin}
          />
        )}
        <div ref={bottomRef} />
      </div>
      <InputBar onSend={onSend} disabled={loading} />
    </div>
  );
}
