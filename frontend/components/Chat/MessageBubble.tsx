import { ChatMessage } from "../../lib/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-accent text-ink rounded-br-sm"
            : "bg-panel text-[#e6e8ec] border border-edge rounded-bl-sm"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
