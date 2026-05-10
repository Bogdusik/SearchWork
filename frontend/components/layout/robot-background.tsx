'use client'

import { SplineScene } from '@/components/ui/splite'
import { Spotlight } from '@/components/ui/spotlight'

export function RobotBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden bg-[#030303]">
      {/* Gradient colour overlays */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.05] via-transparent to-rose-500/[0.05] blur-3xl" />

      {/* 3D Robot scene — full screen */}
      <SplineScene
        scene="https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode"
        className="w-full h-full"
      />

      {/* Gradient overlay so content is readable */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#030303]/90 via-[#030303]/40 to-transparent" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#030303]/60 via-transparent to-[#030303]/60" />

      {/* Mouse-following spotlight */}
      <Spotlight size={400} />
    </div>
  )
}
