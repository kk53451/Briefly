"use client"

import { cn } from "@/lib/utils"
import { Check } from "lucide-react"

interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
}

export function ProgressIndicator({ currentStep, totalSteps }: ProgressIndicatorProps) {
  // 최대 6개 스텝만 표시
  const maxVisibleSteps = 6
  const visibleSteps = Math.min(totalSteps, maxVisibleSteps)

  return (
    <div className="flex items-center justify-center w-full py-4">
      <div className="relative flex items-center justify-between w-full max-w-md">
        {/* 연결선 */}
        <div className="absolute h-0.5 bg-muted w-full z-0"></div>

        {/* 스텝 표시 */}
        {Array.from({ length: visibleSteps }).map((_, index) => {
          const isActive = index + 1 <= currentStep
          const isCurrent = index + 1 === currentStep

          return (
            <div
              key={index}
              className={cn(
                "relative z-10 flex items-center justify-center rounded-full transition-all",
                isActive ? "bg-primary" : "bg-muted",
                isCurrent ? "h-8 w-8" : "h-3 w-3",
              )}
            >
              {isCurrent && <Check className="h-4 w-4 text-primary-foreground" />}
            </div>
          )
        })}
      </div>
    </div>
  )
}
