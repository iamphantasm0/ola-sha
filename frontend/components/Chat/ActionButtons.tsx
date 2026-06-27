"use client";

import { useState } from "react";
import { Action } from "../../lib/types";

const NETWORKS = ["base", "arbitrum", "polygon", "ethereum"];
const inputCls =
  "w-full rounded-lg border border-edge bg-ink px-3 py-2 text-sm text-text outline-none focus:border-gold/50 placeholder:text-muted/60";

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

  const AUTH_REQUIRED = new Set(["use_saved_bank", "use_saved_wallet", "save_bank", "save_wallet"]);

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
      <div className="animate-riseIn mt-1 max-w-sm space-y-2.5 rounded-xl border border-edge bg-panel p-3.5">
        <div className="text-xs uppercase tracking-[0.14em] text-muted">Payout account</div>
        <input className={inputCls} placeholder="Bank name (e.g. GTBank, Kuda)" value={bankName} onChange={(e) => setBankName(e.target.value)} />
        <input className={inputCls} placeholder="Account number" value={acctNum} onChange={(e) => setAcctNum(e.target.value)} />
        <div className="flex gap-2 pt-0.5">
          <button
            disabled={disabled || !bankName || !acctNum}
            onClick={() => {
              onRun("submit_bank", { bank_name: bankName, account_number: acctNum }, `${bankName} ${acctNum}`);
              setForm(null);
            }}
            className="rounded-lg bg-gold px-3.5 py-1.5 text-sm font-medium text-ink disabled:opacity-40"
          >
            Verify account
          </button>
          <button onClick={() => setForm(null)} className="rounded-lg px-3 py-1.5 text-sm text-muted hover:text-text">
            Back
          </button>
        </div>
      </div>
    );
  }

  if (form === "wallet") {
    return (
      <div className="animate-riseIn mt-1 max-w-sm space-y-2.5 rounded-xl border border-edge bg-panel p-3.5">
        <div className="text-xs uppercase tracking-[0.14em] text-muted">Receiving wallet</div>
        <input className={`${inputCls} font-mono`} placeholder="0x… address" value={addr} onChange={(e) => setAddr(e.target.value)} />
        <select className={inputCls} value={net} onChange={(e) => setNet(e.target.value)}>
          {NETWORKS.map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
        <div className="flex gap-2 pt-0.5">
          <button
            disabled={disabled || !addr}
            onClick={() => {
              onRun("submit_wallet", { address: addr, network: net }, `${addr} (${net})`);
              setForm(null);
            }}
            className="rounded-lg bg-gold px-3.5 py-1.5 text-sm font-medium text-ink disabled:opacity-40"
          >
            Add wallet
          </button>
          <button onClick={() => setForm(null)} className="rounded-lg px-3 py-1.5 text-sm text-muted hover:text-text">
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-riseIn mt-1 flex flex-wrap gap-2">
      {actions.map((a, i) => {
        const base = "rounded-full px-4 py-2 text-sm transition-transform hover:-translate-y-px disabled:opacity-40 disabled:hover:translate-y-0";
        const style = a.primary
          ? "bg-gold font-medium text-ink"
          : a.type === "cancel"
          ? "text-muted hover:text-danger"
          : "border border-gold/35 text-gold hover:bg-gold-soft";
        return (
          <button key={i} disabled={disabled} onClick={() => click(a)} className={`${base} ${style}`}>
            {a.label}
          </button>
        );
      })}
    </div>
  );
}
