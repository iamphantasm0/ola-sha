"use client";

import { useState } from "react";
import { Action } from "../../lib/types";

const NETWORKS = ["base", "polygon", "arbitrum", "ethereum", "bnb"];

export function ActionButtons({
  actions,
  authed,
  disabled,
  onRun,
  onRequireLogin,
}: {
  actions: Action[];
  authed: boolean;
  disabled: boolean;
  onRun: (action: string, payload?: Record<string, any>, userEcho?: string) => void;
  onRequireLogin: () => void;
}) {
  const [form, setForm] = useState<null | "bank" | "wallet">(null);
  const [bankName, setBankName] = useState("");
  const [acctNum, setAcctNum] = useState("");
  const [addr, setAddr] = useState("");
  const [net, setNet] = useState("base");

  if (!actions.length && !form) return null;

  const AUTH_REQUIRED = new Set(["use_saved_bank", "use_saved_wallet", "save_bank"]);

  const click = (a: Action) => {
    if (a.type === "enter_bank") return setForm("bank");
    if (a.type === "enter_wallet") return setForm("wallet");
    if (AUTH_REQUIRED.has(a.type) && !authed) return onRequireLogin();
    const echo =
      a.type === "use_saved_bank" || a.type === "use_saved_wallet"
        ? a.label
        : a.type === "confirm_send"
        ? "Confirm"
        : a.type === "cancel"
        ? "Cancel"
        : undefined;
    onRun(a.type, a.payload || {}, echo);
  };

  if (form === "bank") {
    return (
      <div className="mt-2 space-y-2 rounded-xl border border-edge bg-panel p-3">
        <div className="text-xs text-gray-400">Enter your payout bank</div>
        <input
          placeholder="Bank name (e.g. GTBank, Kuda)"
          value={bankName}
          onChange={(e) => setBankName(e.target.value)}
          className="w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <input
          placeholder="Account number"
          value={acctNum}
          onChange={(e) => setAcctNum(e.target.value)}
          className="w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <div className="flex gap-2">
          <button
            disabled={disabled || !bankName || !acctNum}
            onClick={() => {
              onRun("submit_bank", { bank_name: bankName, account_number: acctNum }, `${bankName} ${acctNum}`);
              setForm(null);
            }}
            className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-ink disabled:opacity-40"
          >
            Verify
          </button>
          <button onClick={() => setForm(null)} className="rounded-lg border border-edge px-3 py-1.5 text-sm text-gray-300">
            Back
          </button>
        </div>
      </div>
    );
  }

  if (form === "wallet") {
    return (
      <div className="mt-2 space-y-2 rounded-xl border border-edge bg-panel p-3">
        <div className="text-xs text-gray-400">Enter your wallet</div>
        <input
          placeholder="0x… address"
          value={addr}
          onChange={(e) => setAddr(e.target.value)}
          className="w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        />
        <select
          value={net}
          onChange={(e) => setNet(e.target.value)}
          className="w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm outline-none focus:border-accent"
        >
          {NETWORKS.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <button
            disabled={disabled || !addr}
            onClick={() => {
              onRun("submit_wallet", { address: addr, network: net }, `${addr} (${net})`);
              setForm(null);
            }}
            className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-ink disabled:opacity-40"
          >
            Use wallet
          </button>
          <button onClick={() => setForm(null)} className="rounded-lg border border-edge px-3 py-1.5 text-sm text-gray-300">
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {actions.map((a, i) => (
        <button
          key={i}
          disabled={disabled}
          onClick={() => click(a)}
          className={`rounded-lg px-3 py-1.5 text-sm disabled:opacity-40 ${
            a.primary
              ? "bg-accent font-medium text-ink"
              : a.type === "cancel"
              ? "border border-edge text-gray-400 hover:text-gray-200"
              : "border border-accent/40 text-accent hover:bg-accent/10"
          }`}
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}
