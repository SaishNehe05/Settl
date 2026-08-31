export function formatINR(paise: number): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: rupees % 1 === 0 ? 0 : 2,
  }).format(rupees);
}

export function formatPercent(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

export function formatDate(isoString: string): string {
  if (!isoString) return "-";
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat("en-IN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    return isoString;
  }
}

export function getStatusBadgeConfig(status: string): { bg: string; text: string; border: string } {
  switch (status?.toUpperCase()) {
    case "RECOVERED":
      return { bg: "bg-emerald-950/70", text: "text-emerald-400", border: "border-emerald-800/80" };
    case "READY":
    case "APPROVED":
      return { bg: "bg-sky-950/70", text: "text-sky-400", border: "border-sky-800/80" };
    case "EXECUTING":
    case "WAITING_RESULT":
    case "ANALYZING":
      return { bg: "bg-indigo-950/70", text: "text-indigo-400", border: "border-indigo-800/80" };
    case "ESCALATED":
      return { bg: "bg-amber-950/70", text: "text-amber-400", border: "border-amber-800/80" };
    case "BLOCKED":
    case "STOPPED":
    case "FAILED":
      return { bg: "bg-rose-950/70", text: "text-rose-400", border: "border-rose-800/80" };
    case "NEW":
    default:
      return { bg: "bg-slate-900", text: "text-slate-400", border: "border-slate-800" };
  }
}
