'use client'

import { createContext, useCallback, useContext, useRef, useState, ReactNode } from 'react'

interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error'
}

interface ToastContextValue {
  toast: (message: string, type?: 'success' | 'error') => void
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} })

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const nextId = useRef(0)

  const toast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    const id = ++nextId.current
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div
        className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none"
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map(t => (
          <div
            key={t.id}
            className={`px-4 py-3 rounded-xl text-sm font-medium shadow-2xl border backdrop-blur-xl animate-in slide-in-from-bottom-4 fade-in duration-300 ${
              t.type === 'success'
                ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/20 border-rose-500/30 text-rose-300'
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  return useContext(ToastContext)
}
