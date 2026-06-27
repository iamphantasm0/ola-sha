import { jsPDF } from "jspdf";
import { OrderState } from "./types";

const STEPS = ["Quote", "Details", "Fund", "Settle", "Receipt"];

type RGB = [number, number, number];

const CREAM: RGB = [241, 235, 222];
const INK: RGB = [42, 36, 27];
const MUTED: RGB = [130, 120, 105];
const GOLD: RGB = [201, 162, 75];
const SUCCESS: RGB = [76, 140, 74];
const SUCCESS_BG: RGB = [230, 245, 228];

function fmtFiat(amount: number | null, currency: string | null): string | null {
  if (amount == null || !currency) return null;
  return `${amount.toLocaleString("en-US", { maximumFractionDigits: 2 })} ${currency}`;
}

function fmtCrypto(amount: number | null, token: string | null): string | null {
  if (amount == null || !token) return null;
  return `${amount} ${token}`;
}

function shortRef(id: string): string {
  return id.length > 14 ? `${id.slice(0, 10)}…` : id;
}

function shortHash(h: string): string {
  return h.length > 36 ? `${h.slice(0, 22)}…${h.slice(-6)}` : h;
}

function drawSeal(doc: jsPDF, cx: number, cy: number, r: number) {
  doc.setDrawColor(...GOLD);
  doc.setLineWidth(1.5);
  doc.circle(cx, cy, r, "S");
  doc.setLineWidth(0.75);
  doc.circle(cx, cy, r - 4, "S");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(7);
  doc.setTextColor(...GOLD);
  doc.text("VERIFIED", cx, cy - 10, { align: "center" });
  doc.setFontSize(16);
  doc.text("0G", cx, cy + 2, { align: "center" });
  doc.setFont("helvetica", "normal");
  doc.setFontSize(6);
  doc.text("ON-CHAIN", cx, cy + 12, { align: "center" });
}

function drawRow(doc: jsPDF, y: number, margin: number, pageW: number, label: string, value: string) {
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(...MUTED);
  doc.text(label.toUpperCase(), margin, y);
  doc.setFont("courier", "normal");
  doc.setFontSize(10);
  doc.setTextColor(...INK);
  const lines = doc.splitTextToSize(value, pageW - margin * 2 - 120);
  doc.text(lines, pageW - margin, y, { align: "right" });
  return y + Math.max(16, lines.length * 12);
}

export function downloadReceiptPdf(order: OrderState, origin?: string) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const margin = 48;
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const contentW = pageW - margin * 2;
  let y = margin;

  doc.setFillColor(...CREAM);
  doc.rect(0, 0, pageW, pageH, "F");

  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.setTextColor(...INK);
  doc.text("Statement", margin, y);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(...MUTED);
  doc.text("OLA · 0G", pageW - margin, y, { align: "right" });
  y += 28;

  doc.setFillColor(...SUCCESS_BG);
  doc.roundedRect(margin, y - 12, 78, 20, 10, 10, "F");
  doc.setFillColor(...SUCCESS);
  doc.circle(margin + 12, y - 1, 2.5, "F");
  doc.setFontSize(10);
  doc.setTextColor(...SUCCESS);
  doc.text("Settled", margin + 20, y + 2);
  y += 28;

  const stepW = contentW / STEPS.length;
  STEPS.forEach((name, i) => {
    const x0 = margin + i * stepW;
    doc.setFillColor(...GOLD);
    doc.rect(x0 + 1, y, stepW - 2, 3, "F");
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.setTextColor(...INK);
    doc.text(name.toUpperCase(), x0 + stepW / 2, y + 13, { align: "center" });
  });
  y += 32;

  doc.setDrawColor(180, 170, 155);
  doc.setLineWidth(0.5);
  doc.line(margin, y, pageW - margin, y);
  y += 20;

  const onramp = order.direction === "onramp";
  const typeLabel = onramp ? "Buy · cash → crypto" : order.direction === "offramp" ? "Sell · crypto → cash" : "—";
  const crypto = fmtCrypto(order.amount, order.token);
  const fiat = fmtFiat(order.output_amount, order.currency);

  y = drawRow(doc, y, margin, pageW, "Type", typeLabel);
  if (crypto) y = drawRow(doc, y, margin, pageW, onramp ? "You receive" : "You sell", crypto);
  if (fiat) y = drawRow(doc, y, margin, pageW, onramp ? "You pay" : "You receive", fiat);
  if (order.paycrest_order_id) {
    y = drawRow(doc, y, margin, pageW, "Provider ref", shortRef(order.paycrest_order_id));
  }

  y += 8;
  const boxY = y;
  const boxH = 150;
  doc.setDrawColor(180, 170, 155);
  doc.setLineDashPattern([3, 3], 0);
  doc.roundedRect(margin, boxY, contentW, boxH, 8, 8, "S");
  doc.setLineDashPattern([], 0);

  drawSeal(doc, pageW - margin - 36, boxY + 36, 28);

  let innerY = boxY + 22;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.setTextColor(...INK);
  doc.text("Receipt", margin + 16, innerY);
  innerY += 16;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...MUTED);
  doc.text("Settled and notarized on the 0G network.", margin + 16, innerY);
  innerY += 22;

  if (order.storage_hash) {
    doc.setFontSize(8);
    doc.setTextColor(...MUTED);
    doc.text("0G STORAGE RECORD", margin + 16, innerY);
    innerY += 12;
    doc.setFont("courier", "normal");
    doc.setFontSize(9);
    doc.setTextColor(...INK);
    doc.text(shortHash(order.storage_hash), margin + 16, innerY);
    innerY += 18;
  }

  if (order.registry_tx_hash) {
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(...MUTED);
    doc.text("0G CHAIN SETTLEMENT", margin + 16, innerY);
    innerY += 12;
    doc.setFont("courier", "normal");
    doc.setFontSize(9);
    doc.setTextColor(...INK);
    doc.text(shortHash(order.registry_tx_hash), margin + 16, innerY);
    innerY += 18;
  }

  const verifyId = order.storage_hash ?? order.registry_tx_hash ?? order.order_id;
  const base = origin ?? (typeof window !== "undefined" ? window.location.origin : "");
  const verifyUrl = `${base}/verify?id=${encodeURIComponent(verifyId)}`;
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...INK);
  doc.textWithLink("Verify live on Ola →", margin + 16, innerY, { url: verifyUrl });

  y = boxY + boxH + 24;
  doc.setFontSize(8);
  doc.setTextColor(...MUTED);
  doc.text(`Order ${order.order_id}`, margin, y);
  doc.text("Ola — a Sterling Concierge demo by Vela Labs", margin, y + 12);

  const slug = order.order_id.slice(0, 8);
  doc.save(`ola-receipt-${slug}.pdf`);
}