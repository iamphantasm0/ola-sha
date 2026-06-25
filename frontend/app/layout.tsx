import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ola — AI Crypto ↔ Fiat Exchange",
  description:
    "Swap stablecoins and local currency by chatting with an AI. Powered by 0G + Paycrest. A Sterling Concierge demo by Vela Labs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
