"use client";

import { useEffect, useRef } from "react";

import { ChatMessage } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";

export function ChatWindow({
  messages,
  loading,
}: {
  messages: ChatMessage[];
  loading: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex-1 space-y-3 overflow-y-auto p-4">
      {messages.map((m, i) => (
        <MessageBubble key={i} msg={m} />
      ))}
      {loading && (
        <div className="flex justify-start">
          <div className="rounded-2xl border border-line bg-panel2 px-4 py-2.5 text-sm text-muted">
            Ola is typing…
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
