const FLAGS: Record<string, string> = {
  NGN: "🇳🇬",
  KES: "🇰🇪",
  UGX: "🇺🇬",
  TZS: "🇹🇿",
  MWK: "🇲🇼",
  BRL: "🇧🇷",
};

export function CurrencyBadge({ code }: { code: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-line bg-panel2 px-2 py-0.5 text-xs text-gray-200">
      {FLAGS[code] ?? "🏳️"} {code}
    </span>
  );
}
