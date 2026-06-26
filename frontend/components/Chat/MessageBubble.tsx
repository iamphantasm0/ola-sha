import { Fragment, ReactNode } from "react";
import { ChatMessage, OrderState } from "../../lib/types";
import { SettlementProofCard } from "./SettlementProofCard";

// Minimal inline markdown: **bold**, *italic*, `code`. Newlines are preserved by
// whitespace-pre-wrap on the container, so the deterministic presenter's line breaks
// and "- " bullets render as written.
const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*\n]+\*)/g;

function renderInline(text: string): ReactNode {
  const parts = text.split(INLINE);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded bg-black/30 px-1 py-0.5 font-mono text-[0.85em] text-gold">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return (
        <em key={i} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function MessageBubble({
  message,
  order,
}: {
  message: ChatMessage;
  order?: OrderState | null;
}) {
  const isUser = message.role === "user";
  return (
    <div className={`flex animate-riseIn ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[78%] whitespace-pre-wrap text-[14.5px] leading-relaxed ${
          isUser
            ? "rounded-2xl rounded-br-md bg-gold-soft px-4 py-2.5 text-text ring-1 ring-gold/25"
            : "rounded-2xl rounded-bl-md border border-edge bg-panel px-4 py-3 text-text"
        }`}
      >
        {!isUser && (
          <span className="mb-1 block font-display text-[11px] uppercase tracking-[0.18em] text-gold/70">
            Ola
          </span>
        )}
        {isUser ? message.content : renderInline(message.content)}
        {!isUser && message.proof && <SettlementProofCard proof={message.proof} order={order} />}
      </div>
    </div>
  );
}
