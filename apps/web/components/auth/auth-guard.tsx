"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";

const PUBLIC_PATHS = ["/login"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, isReady, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isReady) return;
    
    // Check for clear query param directly to avoid Next.js Suspense deopts
    if (typeof window !== "undefined" && window.location.search.includes("clear=1")) {
      logout();
      router.replace("/login");
      return;
    }

    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
    
    if (!token && !isPublic) {
      router.replace("/login");
    }
    
    if (token && isPublic) {
      router.replace("/");
    }
  }, [token, isReady, pathname, router, logout]);

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
