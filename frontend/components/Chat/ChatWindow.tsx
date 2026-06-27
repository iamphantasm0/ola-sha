"use client";

import { useEffect, useRef } from "react";
import { Action, ChatMessage, OrderState } from "../../lib/types";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";
import { ActionButtons } from "./ActionButtons";

export function ChatWindow({
  messages,
  actions,
  authed,
  loading,
  settledOrder,
  onSend,
  onRun,
  onRequireLogin,
}: {
  messages: ChatMessage[];
  actions: Action[];
  authed: boolean;
  loading: boolean;
  settledOrder?: OrderState | null;
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
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.map((m, i) => (
            <MessageBubble
              key={i}
              message={m}
              order={
                m.proof && settledOrder?.order_id === m.proof.order_id ? settledOrder : null
              }
            />
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-edge bg-panel px-4 py-3.5">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold/70 [animation-delay:-0.2s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold/70 [animation-delay:-0.1s]" />
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold/70" />
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
      </div>
      <InputBar onSend={onSend} disabled={loading} />
    </div>
  );
}
