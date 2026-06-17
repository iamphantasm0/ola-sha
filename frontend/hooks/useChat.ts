"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchOrder, sendChat } from "../lib/api";
import { getSessionId, resetSession } from "../lib/session";
import { ChatMessage, OrderState, POLLING_STATES, TERMINAL_STATES } from "../lib/types";

const GREETING: ChatMessage = {
  role: "assistant",
  content:
    "Hi, I'm Ola. I help you swap between stablecoins and local currency.\n\nTry: \"sell 200 USDT for NGN\" or \"buy 50 USDT with KES\".",
};

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [order, setOrder] = useState<OrderState | null>(null);
  const [loading, setLoading] = useState(false);
  const sessionRef = useRef<string>("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    sessionRef.current = getSessionId();
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  // Poll the order endpoint while awaiting an external event (deposit/payment/settlement).
  useEffect(() => {
    stopPolling();
    if (!order || !POLLING_STATES.has(order.status)) return;
    pollRef.current = setInterval(async () => {
      try {
        const fresh = await fetchOrder(order.order_id, sessionRef.current);
        setOrder(fresh);
        if (TERMINAL_STATES.has(fresh.status) || !POLLING_STATES.has(fresh.status)) {
          stopPolling();
        }
        if (fresh.status === "SETTLED") {
          setMessages((m) => [
            ...m,
            {
              role: "assistant",
              content: `Transaction complete. Receipt stored on 0G.\nStorage hash: ${fresh.storage_hash ?? "—"}`,
            },
          ]);
        }
      } catch {
        /* transient — keep polling */
      }
    }, 3000);
    return stopPolling;
  }, [order, stopPolling]);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setMessages((m) => [...m, { role: "user", content: trimmed }]);
    setLoading(true);
    try {
      const res = await sendChat(trimmed, sessionRef.current);
      setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
      if (res.order_state) setOrder(res.order_state);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Something went wrong reaching the service. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const newChat = useCallback(() => {
    stopPolling();
    resetSession();
    sessionRef.current = getSessionId();
    setMessages([GREETING]);
    setOrder(null);
  }, [stopPolling]);

  return { messages, order, loading, send, newChat };
}
