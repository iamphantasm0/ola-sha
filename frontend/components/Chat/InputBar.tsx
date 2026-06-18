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
    <div className="px-4 pb-4 pt-2">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-edge bg-panel p-2 focus-within:border-gold/50">
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
          placeholder="Tell Ola what you'd like to do…  e.g. sell 200 USDC for naira"
          className="flex-1 resize-none bg-transparent px-2 py-1.5 text-[14.5px] text-text outline-none placeholder:text-muted/70"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          className="rounded-xl bg-gold px-4 py-2 text-sm font-medium text-ink transition-transform hover:-translate-y-px disabled:opacity-40 disabled:hover:translate-y-0"
        >
          Send
        </button>
      </div>
    </div>
  );
}
