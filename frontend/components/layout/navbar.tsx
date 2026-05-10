'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const links = [
  { href: '/', label: 'Dashboard' },
  { href: '/search', label: 'Search' },
  { href: '/cv', label: 'My CV' },
  { href: '/applications', label: 'Applications' },
]

export function Navbar() {
  const pathname = usePathname()
  return (
    <nav className="relative z-20 flex items-center gap-6 px-6 py-4 border-b border-white/[0.06] bg-black/20 backdrop-blur-md">
      <span className="font-bold text-sm bg-gradient-to-r from-indigo-300 to-rose-300 bg-clip-text text-transparent mr-4">
        SearchWork
      </span>
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={cn(
            'text-sm transition-colors',
            pathname === link.href
              ? 'text-white font-medium'
              : 'text-white/40 hover:text-white/70'
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  )
}
