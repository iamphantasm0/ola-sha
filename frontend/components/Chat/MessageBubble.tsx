import { ChatMessage } from "../../lib/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
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
        {message.content}
      </div>
    </div>
  );
}
