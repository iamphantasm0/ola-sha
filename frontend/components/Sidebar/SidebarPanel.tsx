"use client";

import { useState } from "react";
import { OrderState } from "../../lib/types";
import { HistoryPanel } from "./HistoryPanel";
import { StatusPanel } from "./StatusPanel";

type Tab = "statement" | "history";

export function SidebarPanel({
  order,
  authed,
  userKey,
}: {
  order: OrderState | null;
  authed: boolean;
  userKey?: string | null;
}) {
  const [tab, setTab] = useState<Tab>("statement");

  const active = tab;

  if (!authed) {
    return <StatusPanel order={order} />;
  }

  return (
    <div className="flex h-full flex-col gap-2">
      <div className="flex shrink-0 gap-1 rounded-full border border-edge bg-panel p-1">
        <button
          type="button"
          onClick={() => setTab("statement")}
          className={`flex-1 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors ${
            active === "statement"
              ? "bg-gold text-ink"
              : "text-muted hover:text-text"
          }`}
        >
          Statement
        </button>
        <button
          type="button"
          onClick={() => setTab("history")}
          className={`flex-1 rounded-full px-3 py-1.5 text-[11px] font-medium transition-colors ${
            active === "history"
              ? "bg-gold text-ink"
              : "text-muted hover:text-text"
          }`}
        >
          History
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {active === "history" ? (
          <HistoryPanel refreshKey={userKey ?? undefined} />
        ) : (
          <StatusPanel order={order} />
        )}
      </div>
    </div>
  );
}