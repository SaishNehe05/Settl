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

export function formatCaseStatus(status: string): string {
  switch (status?.toUpperCase()) {
    case 'WAITING_RESULT': return 'Waiting for outcome';
    case 'READY': return 'Ready to recover';
    case 'APPROVED': return 'Approved by policy';
    case 'RECOVERED': return 'Recovered';
    case 'PARTIALLY_RECOVERED': return 'Partially recovered';
    case 'ESCALATED': return 'Needs human review';
    case 'STOPPED': return 'Stopped by guardrails';
    case 'BLOCKED': return 'Blocked';
    case 'ACTION_PENDING': return 'Action pending';
    case 'CUSTOMER_ACTION_REQUIRED': return 'Customer action required';
    case 'VERIFICATION_FAILED': return 'Verification failed';
    case 'ANALYZING': return 'AI analyzing';
    case 'NEW': return 'New event detected';
    case 'EXECUTING': return 'Taking action';
    default: return status || 'Unknown status';
  }
}

export function formatCaseType(type: string): string {
  switch (type?.toUpperCase()) {
    case 'PAYMENT_FAILURE': return 'Payment failed';
    case 'CHECKOUT_ABANDONMENT': return 'Checkout abandoned';
    case 'SUBSCRIPTION_FAILED': return 'Subscription payment failed';
    case 'OVERDUE_RECEIVABLE': return 'Overdue receivable';
    case 'PROMISE_TO_PAY': return 'Promise to pay';
    case 'MANDATE_FAILURE': return 'Recurring payment issue';
    case 'MANUAL_ENTRY': return 'Manual offline entry';
    default: return type || 'Unknown event';
  }
}

export function formatActionType(action: string): string {
  switch (action?.toUpperCase()) {
    case 'CREATE_PAYMENT_LINK': return 'Create payment link';
    case 'SEND_REMINDER': return 'Send reminder email';
    case 'SEND_FOLLOW_UP': return 'Send follow-up notification';
    case 'SEND_PAYMENT_LINK': return 'Send payment link directly';
    case 'CUSTOMER_ACTION_REQUIRED': return 'Prompt customer action';
    case 'WAIT': return 'Monitor and wait';
    case 'MONITOR': return 'Monitor transaction';
    case 'FOLLOW_UP': return 'Schedule follow up';
    case 'CREATE_COLLECTION_CASE': return 'Internal collection case';
    case 'ESCALATE': return 'Escalate to human operator';
    case 'STOP': return 'Stop recovery actions';
    default: return action || 'Unknown action';
  }
}

export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
