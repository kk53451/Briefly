"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter, useSearchParams } from "next/navigation"

const API_BASE_URL = "http://localhost:8000"

export default function KakaoCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState("🔄 로그인 처리 중입니다...")
  const processingRef = useRef(false) // useRef로 더 강력한 중복 방지

  useEffect(() => {
    if (processingRef.current) return // 이미 처리 중이면 중단
    
    const code = searchParams.get("code")
    const error = searchParams.get("error")

    const handleKakaoCallback = async () => {
      processingRef.current = true // 처리 시작 표시
      
      // 카카오에서 오류를 반환한 경우
      if (error) {
        console.error("카카오 로그인 오류:", error)
        setStatus("❌ 카카오 로그인이 취소되었습니다.")
        setTimeout(() => router.push("/"), 3000)
        return
      }

      if (!code) {
        setStatus("❌ 인가 코드가 없습니다.")
        console.error("카카오 인가 코드가 없습니다.")
        setTimeout(() => router.push("/"), 2000)
        return
      }

      try {
        setStatus("🔄 서버와 통신 중...")
        console.log("카카오 인증 코드:", code)
        console.log("코드 길이:", code.length)

        // URL을 정리하여 코드 재사용 방지
        const currentUrl = window.location.href
        const urlWithoutParams = window.location.origin + window.location.pathname
        if (currentUrl !== urlWithoutParams) {
          window.history.replaceState({}, document.title, urlWithoutParams)
          console.log("URL 파라미터 제거 완료")
        }

        const res = await fetch(`${API_BASE_URL}/api/auth/kakao/callback?code=${encodeURIComponent(code)}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        const data = await res.json()
        console.log("백엔드 응답:", data)

        if (!res.ok) {
          console.error("❌ 로그인 실패:", data)
          setStatus("❌ 로그인 실패")
          
          // 특정 오류 메시지 처리
          if (data.detail && (
            data.detail.includes("만료되었거나 이미 사용") || 
            data.detail.includes("이미 사용된 코드")
          )) {
            alert("인증 코드가 만료되었거나 이미 사용되었습니다. 다시 로그인해주세요.")
            router.push("/")
          } else {
            alert(`로그인 실패: ${data.detail || "서버 오류"}`)
            setTimeout(() => router.push("/"), 2000)
          }
          return
        }

        if (data.access_token) {
          // 토큰 및 사용자 정보 저장
          localStorage.setItem("access_token", data.access_token)
          localStorage.setItem("user_id", data.user_id)
          localStorage.setItem("nickname", data.nickname)

          console.log("✅ 로그인 성공:", data)
          setStatus("✅ 로그인 성공! 리디렉션 중...")

          // 온보딩 상태 확인
          try {
            const onboardingRes = await fetch(`${API_BASE_URL}/api/user/onboarding/status`, {
              headers: {
                Authorization: `Bearer ${data.access_token}`,
              },
            })

            if (onboardingRes.ok) {
              const onboardingData = await onboardingRes.json()
              console.log("온보딩 상태:", onboardingData)

              if (onboardingData.onboarded) {
                router.push("/ranking")
              } else {
                router.push("/onboarding")
              }
            } else {
              // 온보딩 상태 확인 실패 시 기본적으로 온보딩으로
              router.push("/onboarding")
            }
          } catch (onboardingError) {
            console.error("온보딩 상태 확인 실패:", onboardingError)
            router.push("/onboarding")
          }
        } else {
          console.warn("⚠️ 응답에 토큰 없음:", data)
          setStatus("❌ 로그인 실패")
          alert("로그인 실패: 응답에 access_token 없음")
          setTimeout(() => router.push("/"), 2000)
        }
      } catch (err) {
        console.error("🚨 로그인 처리 중 예외:", err)
        setStatus("❌ 로그인 중 오류 발생")
        alert("로그인 처리 중 예외 발생")
        setTimeout(() => router.push("/"), 2000)
      }
    }

    handleKakaoCallback()
  }, [searchParams, router])

  return (
    <div className="flex h-screen items-center justify-center">
      <div className="text-center">
        <div className="text-lg font-semibold mb-4">{status}</div>
        {status.includes("처리 중") && (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        )}
        {status.includes("실패") && (
          <div className="mt-4">
            <button 
              onClick={() => router.push("/")}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              홈으로 돌아가기
            </button>
          </div>
        )}
        <div className="mt-4 text-sm text-gray-600">
          페이지를 새로고침하지 마세요
        </div>
      </div>
    </div>
  )
}
