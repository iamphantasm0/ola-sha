"use client";

import { useState } from "react";

export function InputBar({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled?: boolean;
}) {
  const [text, setText] = useState("");

  const submit = () => {
    const t = text.trim();
    if (!t) return;
    onSend(t);
    setText("");
  };

  return (
    <div className="flex gap-2 border-t border-line bg-panel p-3">
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
        placeholder="Type a message…  e.g. sell 200 USDT for NGN"
        className="flex-1 resize-none rounded-xl border border-line bg-ink px-3 py-2 text-sm outline-none focus:border-mint"
      />
      <button
        onClick={submit}
        disabled={disabled}
        className="rounded-xl bg-mint px-4 text-sm font-semibold text-black disabled:opacity-50"
      >
        Send
      </button>
    </div>
  );
}
