"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { verifyOrder, verifyRecent } from "../../lib/api";
import { Settlement } from "../../lib/types";

function short(h?: string | null) {
  if (!h) return "—";
  return `${h.slice(0, 12)}…${h.slice(-8)}`;
}

function SettlementCard({ s }: { s: Settlement }) {
  const [proof, setProof] = useState<Settlement | null>(null);
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

  const amount = s.direction === "onramp" ? `${s.amount} ${s.token}` : `${s.amount} ${s.token}`;
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
          <a href={s.storage_url ?? "#"} target="_blank" rel="noreferrer" className="break-all font-mono text-paper-ink underline decoration-gold/40 hover:decoration-gold">
            {short(s.storage_hash)}
          </a>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">0G Chain settlement</div>
          <a href={s.chain_url ?? "#"} target="_blank" rel="noreferrer" className="break-all font-mono text-paper-ink underline decoration-gold/40 hover:decoration-gold">
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
        <div className="mt-4 space-y-3 rounded-xl border border-dashed border-paper-ink/25 bg-paper-ink/[0.02] p-3 text-[12px]">
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
              {proof.chain?.block ? ` — block ${proof.chain.block.toLocaleString()}, ${proof.chain.events} event(s)` : ""}
            </span>
          </div>
          {proof.storage_record && (
            <pre className="max-h-44 overflow-auto rounded-lg bg-paper-ink/[0.04] p-2 font-mono text-[10px] leading-relaxed text-paper-ink">
              {JSON.stringify(proof.storage_record, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export default function VerifyPage() {
  const [settlements, setSettlements] = useState<Settlement[] | null>(null);

  useEffect(() => {
    verifyRecent().then((d) => setSettlements(d.settlements)).catch(() => setSettlements([]));
  }, []);

  return (
    <main className="ola-bg min-h-screen">
      <header className="flex items-center justify-between border-b border-edge px-5 py-3.5">
        <div className="flex items-baseline gap-3">
          <span className="font-display text-2xl font-semibold tracking-tight text-gold">Ola</span>
          <span className="text-[11px] uppercase tracking-[0.22em] text-muted">Proof of settlement</span>
        </div>
        <Link href="/" className="rounded-full border border-edge px-3.5 py-1.5 text-xs text-muted hover:border-gold/50 hover:text-text">
          ← Back to app
        </Link>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="font-display text-3xl text-text">Proof, not promises.</h1>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
          Every settlement on Ola is notarized on 0G — an immutable record on <b className="text-text">0G Storage</b> and a
          settlement logged on <b className="text-text">0G Chain</b>. Pick any one below and verify it live, against the
          0G network itself. No wallet, no login.
        </p>

        <div className="mt-8 space-y-4">
          {settlements === null && <div className="text-sm text-muted">Loading settlements…</div>}
          {settlements?.length === 0 && (
            <div className="rounded-2xl border border-edge bg-panel p-6 text-sm text-muted">
              No settled transactions yet. Make one on the{" "}
              <Link href="/" className="text-gold underline">app</Link> and it'll appear here, verifiable on 0G.
            </div>
          )}
          {settlements?.map((s) => <SettlementCard key={s.order_id} s={s} />)}
        </div>
      </div>
    </main>
  );
}
