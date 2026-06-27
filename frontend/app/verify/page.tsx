"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useCallback, useEffect, useState } from "react";
import { OgRegistryStats } from "../../components/OgRegistryStats";
import { verifyLookup, verifyOrder, verifyRecent } from "../../lib/api";
import { Settlement } from "../../lib/types";

function short(h?: string | null) {
  if (!h) return "—";
  return `${h.slice(0, 12)}…${h.slice(-8)}`;
}

const MATCHED_LABEL: Record<string, string> = {
  order_id: "order ID",
  storage_hash: "0G Storage hash",
  registry_tx_hash: "0G Chain tx",
  paycrest_order_id: "provider reference",
};

function ProofPanel({ proof }: { proof: Settlement }) {
  return (
    <div className="mt-4 space-y-3 rounded-xl border border-dashed border-paper-ink/25 bg-paper-ink/[0.02] p-3 text-[12px]">
      {proof.matched_by && (
        <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">
          Matched by {MATCHED_LABEL[proof.matched_by] ?? proof.matched_by}
        </div>
      )}
      <div className="flex items-center gap-2">
        <span className="text-success">✓</span>
        <span className="text-paper-ink">
          Retrieved from <b>0G Storage</b> just now {proof.storage_record ? "(record below)" : ""}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className={proof.chain?.verified ? "text-success" : "text-danger"}>
          {proof.chain?.verified ? "✓" : "✗"}
        </span>
        <span className="text-paper-ink">
          Confirmed on <b>0G Chain</b>
          {proof.chain?.block
            ? ` — block ${proof.chain.block.toLocaleString()}, ${proof.chain.events} event(s)`
            : ""}
        </span>
      </div>
      {proof.storage_record && (
        <pre className="max-h-44 overflow-auto rounded-lg bg-paper-ink/[0.04] p-2 font-mono text-[10px] leading-relaxed text-paper-ink">
          {JSON.stringify(proof.storage_record, null, 2)}
        </pre>
      )}
    </div>
  );
}

function SettlementCard({
  s,
  autoProof = false,
}: {
  s: Settlement;
  autoProof?: boolean;
}) {
  const [proof, setProof] = useState<Settlement | null>(autoProof ? s : null);
  const [loading, setLoading] = useState(false);

  const runProof = async () => {
    setLoading(true);
    try {
      setProof(await verifyOrder(s.order_id));
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  const amount = `${s.amount} ${s.token}`;
  const fiat = s.output_amount ? `${s.output_amount.toLocaleString()} ${s.currency}` : "";

  return (
    <div className="paper rounded-2xl p-5">
      <div className="flex items-baseline justify-between border-b border-paper-ink/10 pb-2">
        <span className="font-display text-base text-paper-ink">
          {s.direction === "onramp" ? "Buy" : "Sell"} · {amount}
          {fiat && <span className="text-paper-muted"> ⇄ {fiat}</span>}
        </span>
        <span className="font-mono text-[10px] text-paper-muted">
          {s.settled_at ? new Date(s.settled_at).toLocaleString() : ""}
        </span>
      </div>

      <div className="mt-3 space-y-2 text-[12px]">
        <div>
          <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">0G Storage record</div>
          {/* Merkle root (content address) — not an explorer tx; the decoded record is
              retrieved live from 0G Storage and shown below on this page. */}
          <span className="break-all font-mono text-paper-ink">{short(s.storage_hash)}</span>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">0G Chain settlement</div>
          <a
            href={s.chain_url ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="break-all font-mono text-paper-ink underline decoration-gold/40 hover:decoration-gold"
          >
            {short(s.registry_tx_hash)}
          </a>
        </div>
      </div>

      {!proof ? (
        <button
          onClick={runProof}
          disabled={loading}
          className="mt-4 rounded-full border border-paper-ink/30 px-4 py-1.5 text-xs font-medium text-paper-ink hover:bg-paper-ink/5 disabled:opacity-50"
        >
          {loading ? "Verifying live…" : "Verify live →"}
        </button>
      ) : (
        <ProofPanel proof={proof} />
      )}
    </div>
  );
}

function VerifyPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlId = searchParams.get("id")?.trim() ?? "";

  const [settlements, setSettlements] = useState<Settlement[] | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const [searchInput, setSearchInput] = useState(urlId);
  const [searchResult, setSearchResult] = useState<Settlement | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const fetchById = useCallback(async (id: string) => {
    const trimmed = id.trim();
    if (!trimmed) return;

    setSearchLoading(true);
    setSearchError(null);
    setSearchResult(null);

    try {
      setSearchResult(await verifyLookup(trimmed));
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Lookup failed";
      setSearchError(
        msg.includes("404") || msg.toLowerCase().includes("not found")
          ? "No settled transaction found for that ID."
          : msg.includes("400") || msg.includes("422")
            ? "That doesn't look like a valid ID."
            : "Could not verify that ID. Try again."
      );
    } finally {
      setSearchLoading(false);
    }
  }, []);

  useEffect(() => {
    verifyRecent()
      .then((d) => {
        setSettlements(d.settlements);
        setNextCursor(d.next_cursor);
        setHasMore(d.has_more);
      })
      .catch(() => setSettlements([]));
  }, []);

  useEffect(() => {
    setSearchInput(urlId);
    if (urlId) {
      fetchById(urlId);
    } else {
      setSearchResult(null);
      setSearchError(null);
    }
  }, [urlId, fetchById]);

  const loadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const d = await verifyRecent(nextCursor);
      setSettlements((prev) => [...(prev ?? []), ...d.settlements]);
      setNextCursor(d.next_cursor);
      setHasMore(d.has_more);
    } catch {
      /* ignore */
    } finally {
      setLoadingMore(false);
    }
  };

  const onSearch = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = searchInput.trim();
    if (!trimmed) return;
    router.replace(`/verify?id=${encodeURIComponent(trimmed)}`, { scroll: false });
  };

  const clearSearch = () => {
    setSearchInput("");
    setSearchResult(null);
    setSearchError(null);
    router.replace("/verify", { scroll: false });
  };

  return (
    <main className="ola-bg min-h-screen">
      <header className="flex items-center justify-between border-b border-edge px-5 py-3.5">
        <div className="flex items-baseline gap-3">
          <span className="font-display text-2xl font-semibold tracking-tight text-gold">Ola</span>
          <span className="text-[11px] uppercase tracking-[0.22em] text-muted">Proof of settlement</span>
        </div>
        <Link
          href="/"
          className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted hover:border-gold/50 hover:text-text"
        >
          ← Back to app
        </Link>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="font-display text-3xl text-text">Proof, not promises.</h1>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
          Every settlement on Ola is notarized on 0G — an immutable record on{" "}
          <b className="text-text">0G Storage</b> and a settlement logged on{" "}
          <b className="text-text">0G Chain</b>. Search by ID or pick from recent settlements below.
          No wallet, no login.
        </p>

        <div className="mt-6">
          <OgRegistryStats variant="full" />
        </div>

        <form onSubmit={onSearch} className="mt-8">
          <label htmlFor="verify-search" className="text-[11px] uppercase tracking-[0.14em] text-muted">
            Look up a settlement
          </label>
          <div className="mt-2 flex gap-2">
            <input
              id="verify-search"
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Order ID, storage hash, or chain tx"
              className="min-w-0 flex-1 rounded-xl border border-edge bg-panel px-4 py-2.5 font-mono text-sm text-text placeholder:text-muted/60 focus:border-gold/50 focus:outline-none"
              spellCheck={false}
              autoComplete="off"
            />
            <button
              type="submit"
              disabled={searchLoading || !searchInput.trim()}
              className="shrink-0 rounded-full bg-gold px-5 py-2.5 text-xs font-medium text-ink transition-transform hover:-translate-y-px disabled:opacity-50"
            >
              {searchLoading ? "Verifying…" : "Verify"}
            </button>
          </div>
          <p className="mt-2 text-[11px] text-muted">
            Paste an order ID, 0G Storage hash, 0G Chain tx, or provider reference from your receipt.
          </p>
        </form>

        {searchError && (
          <div className="mt-4 rounded-xl border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">
            {searchError}
          </div>
        )}

        {searchResult && (
          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-lg text-text">Search result</h2>
              <button
                type="button"
                onClick={clearSearch}
                className="text-xs text-muted hover:text-text"
              >
                Clear
              </button>
            </div>
            <SettlementCard s={searchResult} autoProof />
          </div>
        )}

        <div className="mt-10">
          <h2 className="font-display text-lg text-text">Recent settlements</h2>
          <div className="mt-4 space-y-4">
            {settlements === null && <div className="text-sm text-muted">Loading settlements…</div>}
            {settlements?.length === 0 && !searchResult && (
              <div className="rounded-2xl border border-edge bg-panel p-6 text-sm text-muted">
                No settled transactions yet. Make one on the{" "}
                <Link href="/" className="text-gold underline">
                  app
                </Link>{" "}
                and it&apos;ll appear here, verifiable on 0G.
              </div>
            )}
            {settlements?.map((s) => (
              <SettlementCard key={s.order_id} s={s} />
            ))}
            {hasMore && (
              <button
                type="button"
                onClick={loadMore}
                disabled={loadingMore}
                className="w-full rounded-full border border-edge px-4 py-2.5 text-xs text-muted transition-colors hover:border-gold/50 hover:text-text disabled:opacity-50"
              >
                {loadingMore ? "Loading…" : "Load more"}
              </button>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<div className="ola-bg min-h-screen p-10 text-sm text-muted">Loading…</div>}>
      <VerifyPageContent />
    </Suspense>
  );
}