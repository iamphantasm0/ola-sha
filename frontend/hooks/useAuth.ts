"use client";

import { useCallback, useEffect, useState } from "react";
import * as api from "../lib/api";
import { clearAuth, getEmail, getToken, setAuth } from "../lib/auth";

export function useAuth() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    if (getToken()) setEmail(getEmail());
  }, []);

  const login = useCallback(async (e: string, p: string) => {
    const r = await api.login(e, p);
    setAuth(r.token, r.email);
    setEmail(r.email);
  }, []);

  const register = useCallback(async (e: string, p: string) => {
    const r = await api.register(e, p);
    setAuth(r.token, r.email);
    setEmail(r.email);
  }, []);

  const logout = useCallback(() => {
    clearAuth();
    setEmail(null);
  }, []);

  return { email, isAuthed: !!email, login, register, logout };
}
