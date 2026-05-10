interface StatsRowProps {
  totalApplications: number
  responses: number
  bestMatch: number
}

export function StatsRow({ totalApplications, responses, bestMatch }: StatsRowProps) {
  const stats = [
    { label: 'Applications', value: totalApplications, color: 'text-indigo-400' },
    { label: 'Responses', value: responses, color: 'text-emerald-400' },
    { label: 'Best Match', value: `${bestMatch}%`, color: 'text-rose-300' },
  ]
  return (
    <div className="grid grid-cols-3 gap-4 mb-8">
      {stats.map((s) => (
        <div key={s.label} className="glass p-4 text-center">
          <div className={`text-3xl font-bold ${s.color}`}>{s.value}</div>
          <div className="text-xs text-white/30 mt-1 uppercase tracking-widest">{s.label}</div>
        </div>
      ))}
    </div>
  )
}
