// API client: wraps fetch with Base URL + Basic Auth headers from Vite env vars.
// VITE_API_BASE_URL: the Render backend URL (or empty for dev proxy)
// VITE_API_USERNAME / VITE_API_PASSWORD: Basic Auth credentials

export const RENDER_BACKEND_DEFAULT = 'https://razorpay-recovery-agent-rnq8.onrender.com'

const RAW_ENV_URL = (import.meta.env.VITE_API_BASE_URL ?? '').trim()
// If VITE_API_BASE_URL is empty, default directly to the deployed Render backend so the app always works
const BASE_URL = RAW_ENV_URL || RENDER_BACKEND_DEFAULT
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
    if (res.status === 401) {
      throw new Error(`401 Unauthorized: Basic Auth required. Set VITE_API_USERNAME & VITE_API_PASSWORD.`)
    }
    if (body.trim().startsWith('<') || body.includes('<!DOCTYPE') || body.includes('<!doctype')) {
      throw new Error(`${res.status} ${res.statusText}: Received HTML instead of JSON. Backend may be offline or URL misconfigured (${url}).`)
    }
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }

  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    const body = await res.text()
    if (body.trim().startsWith('<') || body.includes('<!DOCTYPE') || body.includes('<!doctype')) {
      throw new Error(
        `Backend returned HTML instead of JSON from ${url}. Ensure backend is running and CORS is allowed.`
      )
    }
    throw new Error(`Expected JSON response from ${path}, received: ${body.slice(0, 100)}`)
  }

  return res.json() as Promise<T>
}

