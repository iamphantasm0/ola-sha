"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchOrder, sendAction, sendChat } from "../lib/api";
import { getSessionId, resetSession } from "../lib/session";
import { Action, ChatMessage, OrderState, POLLING_STATES, SettlementProof, TERMINAL_STATES } from "../lib/types";

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
  const proofShownRef = useRef<Set<string>>(new Set());

  const proofFromOrder = (o: OrderState): SettlementProof | undefined => {
    if (o.status !== "SETTLED" || (!o.storage_hash && !o.registry_tx_hash)) return undefined;
    return {
      order_id: o.order_id,
      storage_hash: o.storage_hash,
      registry_tx_hash: o.registry_tx_hash,
    };
  };

  const appendAssistant = useCallback((content: string, proof?: SettlementProof) => {
    if (proof) {
      if (proofShownRef.current.has(proof.order_id)) return;
      proofShownRef.current.add(proof.order_id);
    }
    setMessages((m) => [...m, { role: "assistant", content, proof }]);
  }, []);

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
          const proof = proofFromOrder(fresh);
          if (proof) {
            appendAssistant(
              "Settled. ✅ Your transaction is complete — notarized on 0G Storage and logged on 0G Chain.",
              proof,
            );
          }
        }
      } catch {
        /* transient */
      }
    }, 3000);
    return stopPolling;
  }, [order, stopPolling, appendAssistant]);

  const apply = useCallback((res: { reply: string; order_state: OrderState | null; actions: Action[] }) => {
    const proof = res.order_state ? proofFromOrder(res.order_state) : undefined;
    let content = res.reply;
    const looksLikeQuote =
      /here'?s your (sell )?quote/i.test(content) || /reply \*\*yes\*\* to confirm/i.test(content);
    if (
      proof &&
      res.order_state?.status === "SETTLED" &&
      !looksLikeQuote &&
      !proofShownRef.current.has(proof.order_id)
    ) {
      if (!content.toLowerCase().includes("settled")) {
        content = `${content}\n\nSettled. ✅ Notarized on 0G.`;
      }
    }
    const showProof = proof && !looksLikeQuote && !proofShownRef.current.has(proof.order_id);
    if (showProof && proof) {
      proofShownRef.current.add(proof.order_id);
      setMessages((m) => [...m, { role: "assistant", content, proof }]);
    } else {
      setMessages((m) => [...m, { role: "assistant", content }]);
    }
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
    proofShownRef.current.clear();
    setMessages([GREETING]);
    setOrder(null);
    setActions([]);
  }, [stopPolling]);

  return { messages, order, actions, loading, send, runAction, newChat };
}
