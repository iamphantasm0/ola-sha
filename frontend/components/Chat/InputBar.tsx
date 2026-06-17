"use client";

import { useState } from "react";

export function InputBar({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [text, setText] = useState("");

  const submit = () => {
    if (!text.trim()) return;
    onSend(text);
    setText("");
  };

  return (
    <div className="flex items-end gap-2 border-t border-edge p-3">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        rows={1}
        placeholder="Message Ola…  (e.g. sell 200 USDT for NGN)"
        className="flex-1 resize-none rounded-xl bg-panel border border-edge px-3 py-2.5 text-sm outline-none focus:border-accent placeholder:text-gray-500"
      />
      <button
        onClick={submit}
        disabled={disabled || !text.trim()}
        className="rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-ink disabled:opacity-40"
      >
        Send
      </button>
    </div>
  );
}
