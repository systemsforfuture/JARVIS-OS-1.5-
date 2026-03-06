// JARVIS 1.5 — API Client

const API_BASE = import.meta.env.VITE_API_URL || '';

let authToken = localStorage.getItem('jarvis_token');

export function getToken() { return authToken; }
export function setToken(t: string) { authToken = t; localStorage.setItem('jarvis_token', t); }
export function clearToken() { authToken = null; localStorage.removeItem('jarvis_token'); }
export function isAuthenticated() { return !!authToken; }

export async function api<T = any>(path: string, options: RequestInit & { body?: any } = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers as Record<string, string> },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  return res.json();
}

export async function login(password: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    if (res.ok) {
      const data = await res.json();
      setToken(data.token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

// WebSocket
let ws: WebSocket | null = null;
let wsListeners: ((data: any) => void)[] = [];

export function connectWS() {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    wsListeners.forEach(fn => fn(data));
  };
  ws.onclose = () => setTimeout(connectWS, 3000);
  return ws;
}

export function onWSMessage(fn: (data: any) => void) {
  wsListeners.push(fn);
  return () => { wsListeners = wsListeners.filter(l => l !== fn); };
}

export function sendWSMessage(data: any) {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}
