"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchOrder, sendChat } from "@/lib/api";
import { getSessionId, resetSession } from "@/lib/session";
import { ChatMessage, OrderState } from "@/lib/types";

const POLL_STATES = new Set([
  "OFFRAMP_AWAITING_DEPOSIT",
  "OFFRAMP_PROCESSING",
  "ONRAMP_AWAITING_PAYMENT",
  "ONRAMP_PROCESSING",
]);

const GREETING =
  'Hey, I\'m Ola. I help you swap stablecoins and local currency.\n\n' +
  '• Sell: "sell 200 USDT for NGN"\n' +
  '• Buy:  "buy 100 USDT with NGN"\n\n' +
  "Corridors: NGN, KES, UGX, TZS, MWK, BRL.";

export function useChat() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [order, setOrder] = useState<OrderState | null>(null);
  const [loading, setLoading] = useState(false);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastStatusRef = useRef<string | null>(null);

  useEffect(() => {
    setSessionId(getSessionId());
  }, []);

  useEffect(() => {
    if (sessionId && messages.length === 0) {
      setMessages([{ role: "assistant", content: GREETING }]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const send = useCallback(
    async (text: string) => {
      if (!text.trim() || !sessionId || loading) return;
      setMessages((m) => [...m, { role: "user", content: text }]);
      setLoading(true);
      try {
        const res = await sendChat(sessionId, text);
        setMessages((m) => [...m, { role: "assistant", content: res.reply }]);
        if (res.order_state) {
          setOrder(res.order_state);
          lastStatusRef.current = res.order_state.status;
        }
      } catch {
        setMessages((m) => [
          ...m,
          { role: "assistant", content: "Sorry — something went wrong. Please try again." },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [sessionId, loading]
  );

  const newChat = useCallback(() => {
    const id = resetSession();
    setSessionId(id);
    setMessages([{ role: "assistant", content: GREETING }]);
    setOrder(null);
    lastStatusRef.current = null;
  }, []);

  // Poll for webhook-driven status changes (settled / failed land out of band).
  useEffect(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    if (!sessionId || !order || !POLL_STATES.has(order.status)) return;

    pollRef.current = setInterval(async () => {
      const o = await fetchOrder(sessionId);
      if (!o) return;
      if (o.status !== lastStatusRef.current) {
        lastStatusRef.current = o.status;
        if (o.status === "SETTLED") {
          setMessages((m) => [...m, { role: "assistant", content: settledMessage(o) }]);
        } else if (o.status === "FAILED") {
          setMessages((m) => [
            ...m,
            { role: "assistant", content: o.last_event_message || "Transaction failed." },
          ]);
        }
      }
      setOrder(o);
    }, 4000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, order?.status]);

  return { sessionId, messages, order, loading, send, newChat };
}

function settledMessage(o: OrderState): string {
  const lines = ["Done — your transaction settled and is now verifiable on 0G.", ""];
  if (o.storage_hash) lines.push(`0G Storage receipt: ${o.storage_hash}`);
  if (o.registry_tx_hash) lines.push(`0G Chain tx: ${o.registry_tx_hash}`);
  return lines.join("\n");
}
