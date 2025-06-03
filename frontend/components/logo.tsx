"use client"

import Link from "next/link"
import Image from "next/image"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"

export function Logo() {
  const { theme, resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // useTheme는 클라이언트 사이드에서만 작동하므로 마운트 여부를 확인
  useEffect(() => {
    setMounted(true)
  }, [])

  // 마운트되지 않았을 때는 기본 로고 표시 (레이아웃 시프트 방지)
  if (!mounted) {
    return (
      <Link href="/" className="flex items-center">
        <div className="h-8 w-[140px]" /> {/* 로고 크기만큼 공간 확보 */}
      </Link>
    )
  }

  // 현재 테마에 따라 로고 선택
  const currentTheme = theme === "system" ? resolvedTheme : theme
  const logoSrc =
    currentTheme === "dark"
      ? "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/darklogo-7rEQHUJi017PCbTZmJpoVdnU5Lrbmn.png"
      : "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/lightlogo-WvXEWuHNiWoWYZPTtWgzNgX4zEimPZ.png"
  const logoAlt = "Briefly - AI 기반 뉴스 오디오 서비스"

  return (
    <Link href="/" className="flex items-center -ml-1.5">
      <Image
        src={logoSrc || "/placeholder.svg"}
        alt={logoAlt}
        width={140}
        height={32}
        priority
        className="h-8 w-auto"
      />
    </Link>
  )
}
