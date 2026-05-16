import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'My Applications',
  description: 'Track all your UK graduate job applications in one place — status, match score, and cover letters.',
}

export default function ApplicationsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
