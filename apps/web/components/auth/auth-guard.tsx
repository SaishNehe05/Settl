"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";

const PUBLIC_PATHS = ["/login"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, isReady } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isReady) return;
    
    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
    
    if (!token && !isPublic) {
      router.replace("/login");
    }
    
    if (token && isPublic) {
      router.replace("/");
    }
  }, [token, isReady, pathname, router]);

  if (!isReady) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-500 text-sm">Loading...</div>
      </div>
    );
  }

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  if (!token && !isPublic) return null;

  return <>{children}</>;
}
