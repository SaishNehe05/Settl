"use client";

import { usePathname } from "next/navigation";
import { AuthProvider } from "@/components/auth/auth-provider";
import AuthGuard from "@/components/auth/auth-guard";
import Navbar from "@/components/layout/navbar";
import Sidebar from "@/components/layout/sidebar";

const PUBLIC_PATHS = ["/login"];

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicPage = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  return (
    <AuthProvider>
      <AuthGuard>
        {isPublicPage ? (
          // Login page: no navbar/sidebar
          <>{children}</>
        ) : (
          // Authenticated pages: full layout
          <>
            <Navbar />
            <div className="flex flex-1">
              <Sidebar />
              <main className="flex-1 overflow-y-auto bg-slate-950 p-6 md:p-8">
                <div className="mx-auto max-w-7xl">{children}</div>
              </main>
            </div>
          </>
        )}
      </AuthGuard>
    </AuthProvider>
  );
}
