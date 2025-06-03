"use client"

import { Toaster } from "sonner"
import { useTheme } from "next-themes"

export function SonnerProvider() {
  const { theme, resolvedTheme } = useTheme()

  // 시스템 테마 또는 사용자 선택 테마에 따라 토스트 테마 결정
  const toastTheme = theme === "system" ? resolvedTheme : theme

  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          fontSize: "14px",
        },
      }}
      theme={toastTheme as "light" | "dark"}
      closeButton
    />
  )
}
