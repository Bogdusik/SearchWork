const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData
  const res = await fetch(`${BASE}${path}`, {
    cache: 'no-store',
    ...init,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...init?.headers,
    },
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json()
}

export const api = {
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
      fetch(`${BASE}/applications/${id}`, { method: 'DELETE' }).then(r => {
        if (!r.ok) throw new Error(`API error ${r.status}`)
      }),
  },
}
