const TOKEN_KEY = "onlychat_token";

// En dev : "" → proxy Vite vers localhost:8000.
// En prod (Railway) : VITE_API_BASE = URL publique du backend.
export const API_BASE = import.meta.env.VITE_API_BASE || "";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

async function req(path, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(API_BASE + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Erreur ${res.status}`);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  login: (email, password) => req("/api/auth/login", { method: "POST", body: { email, password } }),
  register: (body) => req("/api/auth/register", { method: "POST", body }),
  me: () => req("/api/me"),
  agencies: () => req("/api/agencies"),
  members: (a) => req(`/api/agencies/${a}/members`),
  accounts: (a) => req(`/api/agencies/${a}/accounts`),
  dashboard: (a, acc) => req(`/api/agencies/${a}/dashboard${acc ? `?account_id=${acc}` : ""}`),
  tags: (a, acc) => req(`/api/agencies/${a}/accounts/${acc}/tags`),
  conversations: (a, acc, filter = "all", q = "") =>
    req(`/api/agencies/${a}/accounts/${acc}/conversations?filter=${filter}${q ? `&q=${encodeURIComponent(q)}` : ""}`),
  messages: (a, acc, conv) => req(`/api/agencies/${a}/accounts/${acc}/conversations/${conv}/messages`),
  send: (a, acc, conv, body) =>
    req(`/api/agencies/${a}/accounts/${acc}/conversations/${conv}/messages`, { method: "POST", body }),
  updateContact: (a, acc, contact, body) =>
    req(`/api/agencies/${a}/accounts/${acc}/contacts/${contact}`, { method: "PUT", body }),
  vault: (a, acc) => req(`/api/agencies/${a}/accounts/${acc}/vault`),
  qrStart: (a, acc) => req(`/api/agencies/${a}/accounts/${acc}/qr/start`, { method: "POST" }),
};
