import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'My CV',
  description: 'Upload your CV and let Claude AI extract your skills, job titles, and keywords for smarter job matching.',
}

export default function CvLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
