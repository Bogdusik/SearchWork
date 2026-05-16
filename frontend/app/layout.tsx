import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { cn } from '@/lib/utils'
import { RobotBackground } from '@/components/layout/robot-background'
import { Navbar } from '@/components/layout/navbar'
import { AuthProvider } from '@/lib/auth-context'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import { ToastProvider } from '@/components/ui/toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'SearchWork',
    template: '%s · SearchWork',
  },
  description: 'AI-powered UK graduate job tracker. Upload your CV, score job matches across 12 job boards, generate cover letters, and track applications — all in one place.',
  openGraph: {
    siteName: 'SearchWork',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={cn(inter.className, 'bg-[#030303] text-white min-h-screen')}>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[9999] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-indigo-600 focus:text-white focus:text-sm"
        >
          Skip to main content
        </a>
        <AuthProvider>
          <ToastProvider>
            <RobotBackground />
            <div className="relative z-10 flex flex-col min-h-screen">
              <Navbar />
              <main id="main-content" className="flex-1 container mx-auto px-4 sm:px-6 py-8 max-w-5xl">
                <ErrorBoundary>{children}</ErrorBoundary>
              </main>
            </div>
          </ToastProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
