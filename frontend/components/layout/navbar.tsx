'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { MenuToggleIcon } from '@/components/ui/menu-toggle-icon';
import { useScroll } from '@/components/ui/use-scroll';

const links = [
  { href: '/cv', label: 'My CV' },
  { href: '/search', label: 'Search' },
  { href: '/applications', label: 'Applications' },
];

export function Navbar() {
  const [open, setOpen] = React.useState(false);
  const scrolled = useScroll(10);
  const pathname = usePathname();

  React.useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const isActive = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href);

  return (
    <>
      <header
        className={cn(
          'sticky top-0 z-50 w-full border-b transition-all ease-out duration-300',
          scrolled && !open
            ? 'bg-black/50 border-white/[0.10] backdrop-blur-xl shadow-[0_1px_0_rgba(255,255,255,0.04)]'
            : 'bg-black/20 border-white/[0.06] backdrop-blur-md',
          open && 'bg-black/60 backdrop-blur-xl border-white/[0.08]',
        )}
      >
        <nav className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-6">
          <span className="text-sm bg-gradient-to-r from-indigo-300 to-rose-300 bg-clip-text text-transparent select-none">
            SearchWork
          </span>

          {/* Desktop links */}
          <div className="hidden items-center gap-1 md:flex">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm transition-colors duration-150',
                  isActive(link.href)
                    ? 'text-white font-medium bg-white/[0.07]'
                    : 'text-white/40 hover:text-white/75 hover:bg-white/[0.04]',
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Mobile toggle */}
          <button
            onClick={() => setOpen(!open)}
            className="md:hidden min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg border border-white/10 text-white/60 hover:text-white hover:border-white/20 transition-colors"
            aria-label="Toggle menu"
          >
            <MenuToggleIcon open={open} className="size-5" duration={300} />
          </button>
        </nav>
      </header>

      {/* Mobile menu — rendered outside <header> to escape its stacking context */}
      {open && (
        <div className="fixed top-14 inset-x-0 bottom-0 z-[9999] bg-[#030303]/95 backdrop-blur-xl border-t border-white/[0.06] md:hidden flex flex-col">
          <div className="animate-in fade-in zoom-in-95 ease-out duration-200 flex flex-col p-6 gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={cn(
                  'px-4 py-3 rounded-xl text-sm transition-colors',
                  isActive(link.href)
                    ? 'text-white font-medium bg-white/[0.08]'
                    : 'text-white/50 hover:text-white hover:bg-white/[0.05]',
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
