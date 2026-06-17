import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ola — AI Crypto ↔ Fiat Exchange",
  description: "Swap stablecoins and local currency by chat. Powered by 0G.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
