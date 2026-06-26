"use client";

import { useState } from "react";
import { downloadReceiptPdf } from "../../lib/receiptPdf";
import { OrderState } from "../../lib/types";

export function DownloadReceiptButton({
  order,
  className = "",
}: {
  order: OrderState;
  className?: string;
}) {
  const [busy, setBusy] = useState(false);

  const onClick = async () => {
    if (busy) return;
    setBusy(true);
    try {
      downloadReceiptPdf(order);
    } finally {
      setBusy(false);
    }
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={busy}
      className={
        className ||
        "rounded-full border border-gold/40 px-3.5 py-1.5 text-[11px] font-medium text-paper-ink transition-colors hover:bg-gold/10 disabled:opacity-50"
      }
    >
      {busy ? "Preparing…" : "Download PDF"}
    </button>
  );
}