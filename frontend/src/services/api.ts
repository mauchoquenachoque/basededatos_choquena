import type {
  Connection, ConnectionCreate,
  MaskingRule, RuleCreate,
  MaskingJob, JobCreate,
  Summary, User, AuthResponse, DynamicQueryResponse, AuditLogEntry
} from '../types';

/**
 * En `npm run dev`, por defecto se llama al backend en :8000 (CORS) para no depender del proxy /api.
 * Debe coincidir con `uvicorn ... --port 8000` y `scripts/start-local.ps1`.
 * En producción (`vite build`), por defecto `/api/v1` (mismo origen o proxy reverso).
 * Anula con VITE_API_URL (p. ej. otro puerto).
 */
export const RESOLVED_API_BASE =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? 'http://127.0.0.1:8000/api/v1' : '/api/v1');

const BASE = RESOLVED_API_BASE;
const TOKEN_KEY = 'enmask_access_token';

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/** Identidad del API (sin token). Útil para detectar otro servicio en el mismo puerto. */
export type ApiMeta = {
  service: string;
  auth: string;
  api_prefix: string;
  has_register?: boolean;
};

export async function fetchApiMeta(): Promise<ApiMeta | null> {
  const url = `${BASE.replace(/\/$/, '')}/meta`;
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    return r.json();
  } catch {
    return null;
  }
}

function apiBaseHint(): string {
  if (BASE.startsWith('/')) {
    return ' Sirve el front con npm run preview (proxy /api) o define VITE_API_URL al hacer build.';
  }
  return ' Comprueba que uvicorn esté en marcha (p. ej. puerto 8000) y que BACKEND_CORS_ORIGINS en el backend incluya el origen de esta página (localhost y 127.0.0.1 con el puerto del front).';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const url = `${BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      headers,
      ...init,
    });
  } catch (e) {
    throw new Error(`${(e as Error).message || 'Network error'}.${apiBaseHint()}`);
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = error.detail;
    let message: string;
    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail.map((d: { msg?: string }) => d.msg ?? '').filter(Boolean).join('; ') || 'Request failed';
    } else {
      message = 'Request failed';
    }
    if (res.status === 404 && /^not\s*found$/i.test(message.trim())) {
      message = `Not Found (no API en ${url.split('?')[0]}).${apiBaseHint()}`;
    }
    throw new Error(message);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json();
}

// ---- Auth ----
export const registerWithPassword = (email: string, password: string, name: string) =>
  request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });

export const loginWithPassword = (email: string, password: string) =>
  request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

export const getCurrentUser = () => request<User>('/auth/me');

// ---- Connections ----
export const getConnections = () => request<Connection[]>('/connections/');
export const createConnection = (data: ConnectionCreate) =>
  request<Connection>('/connections/', { method: 'POST', body: JSON.stringify(data) });
export const deleteConnection = (id: string) =>
  request<void>(`/connections/${id}`, { method: 'DELETE' });
export const discoverPii = (id: string) =>
  request<RuleCreate[]>(`/connections/${id}/discover`);

// ---- Rules ----
export const getRules = () => request<MaskingRule[]>('/rules/');
export const createRule = (data: RuleCreate) =>
  request<MaskingRule>('/rules/', { method: 'POST', body: JSON.stringify(data) });
export const deleteRule = (id: string) =>
  request<void>(`/rules/${id}`, { method: 'DELETE' });

// ---- Jobs ----
export const getJobs = () => request<MaskingJob[]>('/jobs/');
export const createJob = (data: JobCreate) =>
  request<MaskingJob>('/jobs/', { method: 'POST', body: JSON.stringify(data) });
export const runJob = (id: string) =>
  request<{ message: string }>(`/jobs/${id}/run`, { method: 'POST' });
export const getJob = (id: string) => request<MaskingJob>(`/jobs/${id}`);
export const queryJob = (id: string) =>
  request<DynamicQueryResponse>(`/jobs/${id}/query`);
export const shareJob = (id: string, email: string) =>
  request<{ message: string }>(`/jobs/${id}/share`, { method: 'POST', body: JSON.stringify({ email }) });
export const getAuditLog = (id: string) =>
  request<AuditLogEntry[]>(`/jobs/${id}/audit`);

// ---- Reports ----
export const getSummary = () => request<Summary>('/reports/summary');
