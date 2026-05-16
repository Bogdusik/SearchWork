import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Job Search',
  description: 'Search junior developer and graduate roles across 12 UK job boards. AI scores each result against your CV.',
}

export default function SearchLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
