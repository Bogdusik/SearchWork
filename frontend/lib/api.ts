const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const TOKEN_KEY = 'sw_access_token'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  document.cookie = 'sw_authed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData
  const token = getToken()
  const res = await fetch(`${BASE}${path}`, {
    cache: 'no-store',
    credentials: 'include',
    ...init,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  })

  if (res.status === 401) {
    clearAuth()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json()
}

export const api = {
  auth: {
    register: (email: string, password: string) =>
      req<{ access_token: string; token_type: string }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    login: (email: string, password: string) =>
      req<{ access_token: string; token_type: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    me: () =>
      req<{ id: number; email: string }>('/auth/me'),
    googleUrl: () =>
      req<{ url: string }>('/auth/google/url'),
  },
  cv: {
    get: () => req<import('@/types').CVProfile | null>('/cv'),
    upload: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return req<import('@/types').CVProfile>('/cv', {
        method: 'POST',
        body: form,
      })
    },
    review: (targetRole: string) =>
      req<import('@/types').CVReview>('/cv/review', {
        method: 'POST',
        body: JSON.stringify({ target_role: targetRole }),
      }),
    generateCoverLetter: (externalId: string, source: string, jobTitle: string, company: string, description: string, forceRegenerate = false) =>
      req<{ content: string }>('/cv/cover-letter', {
        method: 'POST',
        body: JSON.stringify({ external_id: externalId, source, job_title: jobTitle, company, description, force_regenerate: forceRegenerate }),
      }).then(d => d.content),
  },
  jobs: {
    search: (q: string, locations: string[] = []) => {
      const params = new URLSearchParams({ q })
      locations.forEach(l => params.append('locations', l))
      return req<import('@/types').JobSearchResult[]>(`/jobs?${params}`)
    },
  },
  applications: {
    list: () => req<import('@/types').Application[]>('/applications'),
    create: (job: import('@/types').JobSearchResult, status: import('@/types').ApplicationStatus) =>
      req<import('@/types').Application>('/applications', {
        method: 'POST',
        body: JSON.stringify({ job, status }),
      }),
    updateStatus: (id: number, status: import('@/types').ApplicationStatus) =>
      req<import('@/types').Application>(`/applications/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
    delete: (id: number) =>
      fetch(`${BASE}/applications/${id}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
      }).then(r => {
        if (r.status === 401) { clearAuth(); window.location.href = '/login' }
        if (!r.ok) throw new Error(`API error ${r.status}`)
      }),
  },
}
