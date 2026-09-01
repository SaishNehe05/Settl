"use client";

import { useAuth } from "@/components/auth/auth-provider";

export function MerchantName({ fallback = "Settl Merchant" }: { fallback?: string }) {
  const { merchant } = useAuth();
  return <>{merchant?.name || fallback}</>;
}
