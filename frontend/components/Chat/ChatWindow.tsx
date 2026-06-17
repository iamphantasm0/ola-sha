"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "../../lib/types";
import { MessageBubble } from "./MessageBubble";
import { InputBar } from "./InputBar";

export function ChatWindow({
  messages,
  loading,
  onSend,
}: {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (text: string) => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm border border-edge bg-panel px-4 py-2.5 text-sm text-gray-400">
              Ola is typing…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <InputBar onSend={onSend} disabled={loading} />
    </div>
  );
}
