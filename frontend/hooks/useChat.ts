"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchOrder, sendAction, sendChat } from "../lib/api";
import { getSessionId, resetSession } from "../lib/session";
import { Action, ChatMessage, OrderState, POLLING_STATES, TERMINAL_STATES } from "../lib/types";

const GREETING: ChatMessage = {
  role: "assistant",
  content:
    "I'm Ola, your stablecoin concierge. Tell me what you'd like to do and I'll handle the rest — every settlement is proven on 0G.\n\nTry: \"sell 200 USDC for naira\", \"buy 50 USDT with shillings\", or ask \"what are the best rates?\". New here? Just say **help**.",
};

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [order, setOrder] = useState<OrderState | null>(null);
  const [actions, setActions] = useState<Action[]>([]);
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

  useEffect(() => {
    stopPolling();
    if (!order || !POLLING_STATES.has(order.status)) return;
    pollRef.current = setInterval(async () => {
      try {
        const fresh = await fetchOrder(order.order_id, sessionRef.current);
        setOrder(fresh);
        if (TERMINAL_STATES.has(fresh.status) || !POLLING_STATES.has(fresh.status)) stopPolling();
        if (fresh.status === "SETTLED") {
          setActions([]);
          setMessages((m) => [
            ...m,
            {
              role: "assistant",
              content: `Settled. ✅ Receipt on 0G.\nStorage hash: ${fresh.storage_hash ?? "—"}`,
            },
          ]);
        }
      } catch {
        /* transient */
      }
    }, 3000);
    return stopPolling;
  }, [order, stopPolling]);

  const apply = useCallback((res: { reply: string; order_state: OrderState | null; actions: Action[] }) => {
    setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
    setOrder(res.order_state);
    setActions(res.actions || []);
  }, []);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setMessages((m) => [...m, { role: "user", content: trimmed }]);
    setLoading(true);
    try {
      apply(await sendChat(trimmed, sessionRef.current));
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }, [loading, apply]);

  const runAction = useCallback(async (action: string, payload: Record<string, any> = {}, userEcho?: string) => {
    if (loading) return;
    if (userEcho) setMessages((m) => [...m, { role: "user", content: userEcho }]);
    setLoading(true);
    try {
      apply(await sendAction(action, sessionRef.current, payload));
    } catch (e: any) {
      setMessages((m) => [...m, { role: "assistant", content: e.message || "That action failed. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }, [loading, apply]);

  const newChat = useCallback(() => {
    stopPolling();
    resetSession();
    sessionRef.current = getSessionId();
    setMessages([GREETING]);
    setOrder(null);
    setActions([]);
  }, [stopPolling]);

  return { messages, order, actions, loading, send, runAction, newChat };
}
