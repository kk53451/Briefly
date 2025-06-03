"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { KakaoLoginButton } from "./kakao-login-button"
import { Logo } from "./logo"
import { UserNav } from "./user-nav"
import { apiClient } from "@/lib/api"
import type { UserProfile } from "@/types/api"
import { ThemeToggle } from "./theme-toggle"

export function PageHeader() {
  const router = useRouter()
  const [user, setUser] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem("access_token")
      if (!token) {
        setUser(null)
        setLoading(false)
        return
      }

      const userData = await apiClient.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error("인증 상태 확인 실패:", error)
      localStorage.removeItem("access_token")
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await apiClient.logout()
      localStorage.removeItem("access_token")
      localStorage.removeItem("user_id")
      localStorage.removeItem("nickname")
      setUser(null)
      router.push("/ranking")
    } catch (error) {
      console.error("로그아웃 실패:", error)
    }
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background">
      <div className="container flex h-16 items-center justify-between max-w-5xl">
        <Logo />
        <div className="flex items-center gap-2">
          <ThemeToggle />
          {loading ? (
            <div className="h-10 w-10"></div>
          ) : user ? (
            <UserNav user={user} onLogout={handleLogout} />
          ) : (
            <KakaoLoginButton />
          )}
        </div>
      </div>
    </header>
  )
}
