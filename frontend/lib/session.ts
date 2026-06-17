// Anonymous session: a UUID persisted in localStorage. No login for MVP.
const KEY = "ola_session_id";

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let id = window.localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(KEY, id);
  }
  return id;
}

export function resetSession(): string {
  const id = crypto.randomUUID();
  if (typeof window !== "undefined") window.localStorage.setItem(KEY, id);
  return id;
}
