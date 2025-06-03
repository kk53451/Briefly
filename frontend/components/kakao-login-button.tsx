"use client"

import { Button } from "@/components/ui/button"

export function KakaoLoginButton() {
  const handleLogin = async () => {
    try {
      // 새로운 콜백 경로로 리디렉션
      window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/auth/kakao/login`
    } catch (error) {
      console.error("로그인 실패:", error)
    }
  }

  return (
    <Button
      onClick={handleLogin}
      className="bg-[#FEE500] text-black hover:bg-[#FEE500]/90 dark:bg-[#FEE500] dark:text-black dark:hover:bg-[#FEE500]/80"
    >
      카카오 로그인
    </Button>
  )
}
