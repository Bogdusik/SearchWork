'use client'

import { useEffect, useState } from 'react'
import { api, apiErrorDetail } from '@/lib/api'
import type { AlertSettings as AlertSettingsData, AlertSettingsInput } from '@/types'

const TOPIC_PATTERN = /^[A-Za-z0-9_-]{8,64}$/
const MAX_CITIES = 10

interface FormState {
  enabled: boolean
  query: string
  cities: string
  minScore: string
  topic: string
}

type FieldErrors = Partial<Record<'query' | 'cities' | 'minScore' | 'topic', string>>
type Status = { kind: 'idle' } | { kind: 'busy' } | { kind: 'ok'; text: string } | { kind: 'error'; text: string }

const EMPTY_FORM: FormState = { enabled: false, query: '', cities: '', minScore: '70', topic: '' }

function toForm(s: AlertSettingsData): FormState {
  return {
    enabled: s.enabled,
    query: s.query,
    cities: s.locations.join(', '),
    minScore: String(s.min_score),
    topic: s.ntfy_topic,
  }
}

function parseCities(raw: string): string[] {
  return raw.split(',').map((c) => c.trim()).filter(Boolean)
}

function validate(form: FormState): { errors: FieldErrors; payload?: AlertSettingsInput } {
  const errors: FieldErrors = {}
  const query = form.query.trim()
  const locations = parseCities(form.cities)
  const minScore = Number(form.minScore)

  if (!query) errors.query = 'Enter a search query'
  else if (query.length > 200) errors.query = 'Keep the query under 200 characters'
  if (locations.length > MAX_CITIES) errors.cities = `Up to ${MAX_CITIES} cities`
  if (form.minScore.trim() === '' || !Number.isInteger(minScore) || minScore < 0 || minScore > 100) {
    errors.minScore = 'Whole number from 0 to 100'
  }
  if (!TOPIC_PATTERN.test(form.topic)) errors.topic = 'Topic must be 8-64 characters: letters, numbers, - or _'

  if (Object.keys(errors).length > 0) return { errors }
  return { errors, payload: { enabled: form.enabled, query, locations, min_score: minScore, ntfy_topic: form.topic } }
}

function randomTopic(): string {
  const bytes = new Uint8Array(12)
  crypto.getRandomValues(bytes)
  return `sw-${Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')}`
}

const inputClass =
  'w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-indigo-500/50 aria-invalid:border-rose-500/60'

function FieldError({ id, text }: { id: string; text?: string }) {
  if (!text) return null
  return <p id={id} className="text-rose-400 text-xs mt-1">{text}</p>
}

function StatusLine({ status }: { status: Status }) {
  if (status.kind === 'ok') return <p className="text-emerald-400 text-xs">{status.text}</p>
  if (status.kind === 'error') return <p className="text-rose-400 text-xs">{status.text}</p>
  return null
}

export function AlertSettings() {
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [hasSaved, setHasSaved] = useState(false)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [saveStatus, setSaveStatus] = useState<Status>({ kind: 'idle' })
  const [testStatus, setTestStatus] = useState<Status>({ kind: 'idle' })

  useEffect(() => {
    api.alerts.get()
      .then((s) => {
        if (s) {
          setForm(toForm(s))
          setHasSaved(true)
        }
      })
      .catch(() => setLoadError(true))
      .finally(() => setLoading(false))
  }, [])

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }))
    setSaveStatus({ kind: 'idle' })
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    const { errors: found, payload } = validate(form)
    setErrors(found)
    if (!payload) return
    setSaveStatus({ kind: 'busy' })
    try {
      const saved = await api.alerts.save(payload)
      setForm(toForm(saved))
      setHasSaved(true)
      setSaveStatus({ kind: 'ok', text: 'Alerts saved' })
    } catch (err) {
      setSaveStatus({ kind: 'error', text: apiErrorDetail(err, 'Could not save alerts. Please try again.') })
    }
  }

  async function handleTest() {
    setTestStatus({ kind: 'busy' })
    try {
      await api.alerts.sendTest()
      setTestStatus({ kind: 'ok', text: 'Test push sent. Check your phone.' })
    } catch (err) {
      setTestStatus({ kind: 'error', text: apiErrorDetail(err, 'Test push failed. Please try again.') })
    }
  }

  return (
    <section data-testid="alert-settings" className="glass p-5 mt-8 space-y-4" aria-labelledby="alerts-heading">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="alerts-heading" className="text-sm font-semibold text-white/80">Job alerts</h2>
          <p className="text-xs text-white/40 mt-1">
            SearchWork re-runs this search in the background a few times a day and pushes new jobs that match your CV to your phone via{' '}
            <a href="https://ntfy.sh" target="_blank" rel="noreferrer" className="text-indigo-300 hover:text-indigo-200 underline underline-offset-2">ntfy</a>.
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={form.enabled}
          aria-label="Alerts enabled"
          onClick={() => update('enabled', !form.enabled)}
          disabled={loading}
          className={`relative shrink-0 h-6 w-11 rounded-full border transition-colors disabled:opacity-40 ${
            form.enabled ? 'bg-indigo-500 border-indigo-400' : 'bg-white/5 border-white/15'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 h-4.5 w-4.5 rounded-full bg-white shadow transition-transform motion-reduce:transition-none ${
              form.enabled ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {loading && <p className="text-xs text-white/30">Loading alert settings…</p>}
      {loadError && <p className="text-rose-400 text-xs">Could not load alert settings. You can still save new ones.</p>}

      <form onSubmit={handleSave} noValidate className="space-y-3">
        <div>
          <label htmlFor="alert-query" className="block text-xs text-white/50 mb-1">Search query</label>
          <input
            id="alert-query"
            type="text"
            value={form.query}
            onChange={(e) => update('query', e.target.value)}
            placeholder="e.g. junior python developer"
            aria-invalid={!!errors.query}
            aria-describedby={errors.query ? 'alert-query-error' : undefined}
            className={inputClass}
          />
          <FieldError id="alert-query-error" text={errors.query} />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[1fr_8rem] gap-3">
          <div>
            <label htmlFor="alert-cities" className="block text-xs text-white/50 mb-1">Cities</label>
            <input
              id="alert-cities"
              type="text"
              value={form.cities}
              onChange={(e) => update('cities', e.target.value)}
              placeholder="Glasgow, Edinburgh (empty = default cities)"
              aria-invalid={!!errors.cities}
              aria-describedby={errors.cities ? 'alert-cities-error' : undefined}
              className={inputClass}
            />
            <FieldError id="alert-cities-error" text={errors.cities} />
          </div>
          <div>
            <label htmlFor="alert-min-score" className="block text-xs text-white/50 mb-1">Minimum match score</label>
            <input
              id="alert-min-score"
              type="number"
              inputMode="numeric"
              min={0}
              max={100}
              value={form.minScore}
              onChange={(e) => update('minScore', e.target.value)}
              aria-invalid={!!errors.minScore}
              aria-describedby={errors.minScore ? 'alert-min-score-error' : undefined}
              className={inputClass}
            />
            <FieldError id="alert-min-score-error" text={errors.minScore} />
          </div>
        </div>

        <div>
          <label htmlFor="alert-topic" className="block text-xs text-white/50 mb-1">ntfy topic</label>
          <div className="flex gap-2">
            <input
              id="alert-topic"
              type="text"
              value={form.topic}
              onChange={(e) => update('topic', e.target.value.trim())}
              placeholder="sw-…"
              autoComplete="off"
              spellCheck={false}
              aria-invalid={!!errors.topic}
              aria-describedby={errors.topic ? 'alert-topic-error' : 'alert-topic-hint'}
              className={`${inputClass} font-mono min-w-0`}
            />
            <button
              type="button"
              onClick={() => update('topic', randomTopic())}
              className="shrink-0 px-3 rounded-lg text-xs font-medium border border-white/10 text-white/60 hover:text-white hover:border-white/20 transition-colors"
            >
              Generate
            </button>
          </div>
          <FieldError id="alert-topic-error" text={errors.topic} />
          {!errors.topic && (
            <p id="alert-topic-hint" className="text-xs text-white/30 mt-1">
              Anyone who knows the topic can read it, so use a long random one. Subscribe to it in the ntfy app.
            </p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-2 pt-1">
          <button
            type="submit"
            disabled={loading || saveStatus.kind === 'busy'}
            className="flex-1 py-2 rounded-lg text-sm font-medium bg-indigo-500 text-white hover:bg-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {saveStatus.kind === 'busy' ? 'Saving…' : 'Save alerts'}
          </button>
          <button
            type="button"
            onClick={handleTest}
            disabled={!hasSaved || testStatus.kind === 'busy'}
            className="flex-1 py-2 rounded-lg text-sm font-medium border border-white/10 text-white/60 hover:text-white hover:border-white/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {testStatus.kind === 'busy' ? 'Sending…' : 'Send test push'}
          </button>
        </div>
        <StatusLine status={saveStatus} />
        <StatusLine status={testStatus} />
      </form>
    </section>
  )
}
