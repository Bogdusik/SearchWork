const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
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
        headers: {},
      })
    },
  },
  jobs: {
    search: (q: string) => req<import('@/types').Job[]>(`/jobs?q=${encodeURIComponent(q)}`),
  },
  applications: {
    list: () => req<import('@/types').Application[]>('/applications'),
    create: (jobId: number, status: import('@/types').ApplicationStatus) =>
      req<import('@/types').Application>('/applications', {
        method: 'POST',
        body: JSON.stringify({ job_id: jobId, status }),
      }),
    updateStatus: (id: number, status: import('@/types').ApplicationStatus) =>
      req<import('@/types').Application>(`/applications/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }),
  },
}
