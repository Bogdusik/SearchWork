import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { cn } from '@/lib/utils'
import { RobotBackground } from '@/components/layout/robot-background'
import { Navbar } from '@/components/layout/navbar'
import { AuthProvider } from '@/lib/auth-context'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SearchWork',
  description: 'AI-powered UK graduate job finder',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={cn(inter.className, 'bg-[#030303] text-white min-h-screen')}>
        <AuthProvider>
          <RobotBackground />
          <div className="relative z-10 flex flex-col min-h-screen">
            <Navbar />
            <main className="flex-1 container mx-auto px-4 sm:px-6 py-8 max-w-5xl">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  )
}
