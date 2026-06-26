"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchOrderHistory } from "../../lib/api";
import { HistoryOrder } from "../../lib/types";
import { DownloadReceiptButton } from "./DownloadReceiptButton";

const STATUS_STYLE: Record<string, string> = {
  SETTLED: "bg-success/15 text-success",
  FAILED: "bg-danger/15 text-danger",
  CANCELLED: "bg-paper-ink/10 text-paper-muted",
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function rampSummary(o: HistoryOrder) {
  const onramp = o.direction === "onramp";
  const crypto = o.amount != null && o.token ? `${o.amount} ${o.token}` : null;
  const fiat =
    o.output_amount != null && o.currency
      ? `${o.output_amount.toLocaleString()} ${o.currency}`
      : null;
  if (onramp && crypto && fiat) return `${fiat} → ${crypto}`;
  if (!onramp && crypto && fiat) return `${crypto} → ${fiat}`;
  return crypto ?? fiat ?? "Ramp";
}

function toOrderState(o: HistoryOrder) {
  return {
    order_id: o.order_id,
    status: o.status,
    direction: o.direction,
    amount: o.amount,
    token: o.token,
    currency: o.currency,
    output_amount: o.output_amount,
    deposit_address: o.deposit_address,
    storage_hash: o.storage_hash,
    registry_tx_hash: o.registry_tx_hash,
    paycrest_order_id: o.paycrest_order_id,
  };
}

export function HistoryPanel({ refreshKey }: { refreshKey?: string }) {
  const [orders, setOrders] = useState<HistoryOrder[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (next?: string) => {
    const isMore = !!next;
    if (isMore) setLoadingMore(true);
    else setLoading(true);
    setError(null);
    try {
      const res = await fetchOrderHistory(next);
      setOrders((prev) => (isMore ? [...prev, ...res.orders] : res.orders));
      setCursor(res.next_cursor);
      setHasMore(res.has_more);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Could not load history";
      setError(
        msg.includes("401") || msg.toLowerCase().includes("not authenticated")
          ? "Session expired — sign in again."
          : msg,
      );
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <div className="paper paper-lines flex h-full flex-col rounded-2xl p-5">
      <div className="flex items-baseline justify-between border-b border-paper-ink/10 pb-3">
        <span className="font-display text-lg text-paper-ink">History</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-paper-muted">
          Your ramps
        </span>
      </div>

      {loading && (
        <div className="mt-8 text-sm text-paper-muted">Loading your ramps…</div>
      )}

      {error && !loading && (
        <div className="mt-6 space-y-3">
          <p className="text-sm text-danger">{error}</p>
          <button
            type="button"
            onClick={() => load()}
            className="text-sm text-paper-ink underline decoration-gold/40"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && orders.length === 0 && (
        <div className="mt-8 text-sm leading-relaxed text-paper-muted">
          No ramps yet.
          <br />
          Complete a buy or sell while signed in and it will show up here.
        </div>
      )}

      {!loading && !error && orders.length > 0 && (
        <div className="mt-3 min-h-0 flex-1 space-y-3 overflow-y-auto pr-0.5">
          {orders.map((o) => {
            const settled = o.status === "SETTLED";
            const verifyId = o.storage_hash ?? o.registry_tx_hash ?? o.order_id;
            const canPdf = settled && (o.storage_hash || o.registry_tx_hash);
            return (
              <div
                key={o.order_id}
                className="rounded-xl border border-paper-ink/12 bg-paper-ink/[0.02] p-3.5"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="font-mono text-[13px] text-paper-ink">{rampSummary(o)}</div>
                    <div className="mt-1 text-[10px] text-paper-muted">
                      {o.direction === "onramp" ? "Buy" : "Sell"} · {formatDate(o.updated_at)}
                    </div>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      STATUS_STYLE[o.status] ?? "bg-paper-ink/8 text-paper-ink"
                    }`}
                  >
                    {o.status === "SETTLED" ? "Settled" : o.status.charAt(0) + o.status.slice(1).toLowerCase()}
                  </span>
                </div>

                {settled && (o.storage_hash || o.registry_tx_hash) && (
                  <div className="mt-2.5 space-y-1 font-mono text-[10px] text-paper-muted">
                    {o.storage_hash && (
                      <div className="truncate">Storage: {o.storage_hash.slice(0, 18)}…</div>
                    )}
                    {o.registry_tx_hash && (
                      <div className="truncate">Chain: {o.registry_tx_hash.slice(0, 18)}…</div>
                    )}
                  </div>
                )}

                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {canPdf && <DownloadReceiptButton order={toOrderState(o)} />}
                  {settled && verifyId && (
                    <Link
                      href={`/verify?id=${encodeURIComponent(verifyId)}`}
                      className="text-[11px] text-paper-ink underline decoration-gold/40 underline-offset-2 hover:decoration-gold"
                    >
                      Verify →
                    </Link>
                  )}
                </div>
              </div>
            );
          })}

          {hasMore && (
            <button
              type="button"
              disabled={loadingMore}
              onClick={() => cursor && load(cursor)}
              className="w-full rounded-full border border-paper-ink/20 py-2 text-xs text-paper-ink transition-colors hover:border-gold/50 disabled:opacity-50"
            >
              {loadingMore ? "Loading…" : "Load more"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}