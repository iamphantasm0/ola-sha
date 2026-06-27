"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchRegistryStats } from "../lib/api";
import { RegistryStats } from "../lib/types";

function fmtUsd(n: number) {
  return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function StatCell({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[10px] uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className="font-display text-xl text-text">{value}</div>
      {sub && <div className="mt-0.5 text-[10px] text-muted">{sub}</div>}
    </div>
  );
}

export function OgRegistryStats({ variant = "full" }: { variant?: "compact" | "full" }) {
  const [stats, setStats] = useState<RegistryStats | null>(null);

  useEffect(() => {
    fetchRegistryStats()
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  if (!stats?.configured) return null;

  const corridorCount = stats.corridors.length;
  const buys = stats.by_direction.onramp ?? 0;
  const sells = stats.by_direction.offramp ?? 0;

  if (variant === "compact") {
    return (
      <div className="rounded-2xl border border-edge bg-panel/80 p-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className="text-[10px] uppercase tracking-[0.14em] text-muted">0G Chain · live</span>
          {stats.contract_url && (
            <a
              href={stats.contract_url}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[9px] text-gold/80 hover:text-gold"
            >
              Registry ↗
            </a>
          )}
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2">
          <StatCell label="Settled" value={String(stats.total_settlements)} />
          <StatCell label="Volume" value={`$${fmtUsd(stats.total_volume_usd)}`} />
          <StatCell label="Corridors" value={String(corridorCount)} />
        </div>
        <p className="mt-2.5 text-[10px] leading-relaxed text-muted">
          {buys} buys · {sells} sells — logged on{" "}
          <Link href="/verify" className="text-gold underline decoration-gold/40">
            OlaRegistry
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-edge bg-panel p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-edge pb-3">
        <div>
          <h2 className="font-display text-lg text-text">0G Chain · live registry</h2>
          <p className="mt-1 text-xs text-muted">
            Every settlement is logged to{" "}
            <span className="text-text">OlaRegistry</span> on Galileo testnet — public, append-only proof
            that Ola moved real money.
          </p>
        </div>
        {stats.contract_url && (
          <a
            href={stats.contract_url}
            target="_blank"
            rel="noreferrer"
            className="shrink-0 rounded-full border border-edge px-3 py-1 text-[10px] text-muted hover:border-gold/50 hover:text-gold"
          >
            View contract ↗
          </a>
        )}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCell
          label="Total settlements"
          value={String(stats.total_settlements)}
          sub="totalSettlements()"
        />
        <StatCell
          label="Volume settled"
          value={`$${fmtUsd(stats.total_volume_usd)}`}
          sub="USD notional on-chain"
        />
        <StatCell label="Buy (onramp)" value={String(buys)} />
        <StatCell label="Sell (offramp)" value={String(sells)} />
      </div>

      {stats.corridors.length > 0 && (
        <div className="mt-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-muted">Corridors used</div>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full min-w-[280px] text-left text-xs">
              <thead>
                <tr className="border-b border-edge text-muted">
                  <th className="pb-2 pr-4 font-normal">Currency</th>
                  <th className="pb-2 pr-4 font-normal">Settlements</th>
                  <th className="pb-2 font-normal">Volume (USD)</th>
                </tr>
              </thead>
              <tbody>
                {stats.corridors.map((c) => (
                  <tr key={c.currency} className="border-b border-edge/60 text-text">
                    <td className="py-2 pr-4 font-mono">{c.currency}</td>
                    <td className="py-2 pr-4">{c.count}</td>
                    <td className="py-2">${fmtUsd(c.volume_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {stats.fetched_at && (
        <p className="mt-4 font-mono text-[10px] text-muted">
          Pulled live from 0G Chain · {stats.fetched_at}
          {stats.events_indexed != null && stats.events_indexed !== stats.total_settlements
            ? ` · ${stats.events_indexed} OrderSettled events`
            : ""}
        </p>
      )}
    </div>
  );
}