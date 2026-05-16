import type { ApplicationStatus } from '@/types'

export const STATUS_OPTIONS: { value: ApplicationStatus; label: string }[] = [
  { value: 'saved', label: 'Saved' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'applied', label: 'Applied' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'rejected', label: 'Rejected' },
]

export const STATUS_COLORS: Record<ApplicationStatus, string> = {
  saved: 'text-white/40',
  in_progress: 'text-amber-400',
  applied: 'text-emerald-400',
  interview: 'text-indigo-400',
  offer: 'text-yellow-300',
  rejected: 'text-rose-400',
}

export const STATUS_LABELS: Record<string, string> = {
  saved: 'Saved',
  in_progress: 'In Progress',
  applied: 'Applied',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
}
