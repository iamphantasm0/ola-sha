import { ChatMessage } from "@/lib/types";

export function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[82%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-mint text-black"
            : "border border-line bg-panel2 text-gray-100"
        }`}
      >
        {msg.content}
      </div>
    </div>
  );
}
