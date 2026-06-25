const KEY = "ola_session_id";

export function getSessionId(): string {
  if (typeof window === "undefined") return "";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

export function resetSession(): string {
  const id = crypto.randomUUID();
  if (typeof window !== "undefined") localStorage.setItem(KEY, id);
  return id;
}
