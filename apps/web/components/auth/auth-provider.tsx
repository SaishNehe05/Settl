"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getToken, getMerchant, setAuth, clearAuth, MerchantInfo } from "@/lib/auth";

interface AuthContextType {
  token: string | null;
  merchant: MerchantInfo | null;
  login: (token: string, merchant: MerchantInfo) => void;
  logout: () => void;
  isReady: boolean;
}

const AuthContext = createContext<AuthContextType>({
  token: null,
  merchant: null,
  login: () => {},
  logout: () => {},
  isReady: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [merchant, setMerchant] = useState<MerchantInfo | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    setToken(getToken());
    setMerchant(getMerchant());
    setIsReady(true);
  }, []);

  const login = (newToken: string, newMerchant: MerchantInfo) => {
    setAuth(newToken, newMerchant);
    setToken(newToken);
    setMerchant(newMerchant);
  };

  const logout = () => {
    clearAuth();
    setToken(null);
    setMerchant(null);
  };

  return (
    <AuthContext.Provider value={{ token, merchant, login, logout, isReady }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
