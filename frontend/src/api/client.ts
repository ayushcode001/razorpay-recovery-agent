// API client — wraps fetch with Base URL + Basic Auth headers from Vite env vars.
// VITE_API_BASE_URL: the Render backend URL (or empty for dev proxy)
// VITE_API_USERNAME / VITE_API_PASSWORD: Basic Auth credentials

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const API_USER = import.meta.env.VITE_API_USERNAME ?? ''
const API_PASS = import.meta.env.VITE_API_PASSWORD ?? ''

function getAuthHeader(): Record<string, string> {
  if (!API_USER || !API_PASS) return {}
  const encoded = btoa(`${API_USER}:${API_PASS}`)
  return { Authorization: `Basic ${encoded}` }
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
      ...(options.headers ?? {}),
    },
  })

  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }

  return res.json() as Promise<T>
}
