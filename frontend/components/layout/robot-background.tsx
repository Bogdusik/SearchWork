'use client'

import { SplineScene } from '@/components/ui/splite'
import { useRef, useEffect } from 'react'

export function RobotBackground() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const canvas = containerRef.current?.querySelector('canvas')
      if (!canvas) return
      canvas.dispatchEvent(new PointerEvent('pointermove', {
        bubbles: false,
        cancelable: true,
        clientX: e.clientX,
        clientY: e.clientY,
        screenX: e.screenX,
        screenY: e.screenY,
        movementX: e.movementX,
        movementY: e.movementY,
        pointerId: 1,
        pointerType: 'mouse',
        view: window,
      }))
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div ref={containerRef} className="robot-bg fixed inset-0 z-0 overflow-hidden bg-[#030303]">
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-indigo-500/[0.05] via-transparent to-rose-500/[0.05] blur-3xl" />
      <SplineScene
        scene="https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode"
        className="w-full h-full"
      />
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-[#030303]/90 via-[#030303]/40 to-transparent" />
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-t from-[#030303]/60 via-transparent to-[#030303]/60" />
    </div>
  )
}
