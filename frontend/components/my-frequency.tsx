"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { FrequencyCard } from "./frequency-card"
import { FrequencyHistory } from "./frequency-history"
import { apiClient } from "@/lib/api"
import type { FrequencyItem } from "@/types/api"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { CATEGORY_MAP, REVERSE_CATEGORY_MAP } from "@/lib/constants"

export function MyFrequency() {
  const router = useRouter()
  const [todayFrequencies, setTodayFrequencies] = useState<FrequencyItem[]>([])
  const [historyFrequencies, setHistoryFrequencies] = useState<FrequencyItem[]>([])
  const [userCategories, setUserCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  useEffect(() => {
    if (isLoggedIn) {
      fetchTodayFrequencies()
      fetchUserCategories()
      fetchHistoryFrequencies()
    }
  }, [isLoggedIn])

  const checkAuthStatus = () => {
    const token = localStorage.getItem("access_token")
    setIsLoggedIn(!!token)
  }

  const fetchTodayFrequencies = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const data = await apiClient.getUserFrequencies()
      
      if (Array.isArray(data)) {
        setTodayFrequencies(data)
      } else {
        setTodayFrequencies([])
      }
    } catch (error) {
      console.error("오늘 주파수 조회 실패:", error)
      setError("주파수 데이터를 불러오는데 실패했습니다. 잠시 후 다시 시도해주세요.")
      setTodayFrequencies([])
    } finally {
      setLoading(false)
    }
  }

  const fetchHistoryFrequencies = async () => {
    try {
      setHistoryLoading(true)
      
      const data = await apiClient.getFrequencyHistory(30)
      
      if (Array.isArray(data)) {
        setHistoryFrequencies(data)
      } else {
        setHistoryFrequencies([])
      }
    } catch (error) {
      console.error("주파수 히스토리 조회 실패:", error)
      // 히스토리는 필수가 아니므로 에러를 숨김
      setHistoryFrequencies([])
    } finally {
      setHistoryLoading(false)
    }
  }

  const fetchUserCategories = async () => {
    try {
      const response = await apiClient.getUserCategories()
      const interests = response?.interests || []
      setUserCategories(interests)
    } catch (error) {
      console.error("카테고리 조회 실패:", error)
      // 기본 카테고리 설정
      setUserCategories(["정치", "경제", "IT/과학"])
    }
  }

  if (!isLoggedIn) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">내 주파수</h1>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>내 주파수를 이용하려면 로그인이 필요합니다.</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">내 주파수</h1>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">내 주파수</h1>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={fetchTodayFrequencies} className="w-full">
          다시 시도
        </Button>
      </div>
    )
  }

  if (!userCategories || userCategories.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">내 주파수</h1>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>관심 있는 뉴스 분야를 먼저 선택해 주세요.</AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/profile/categories")} className="w-full">
          카테고리 설정하기
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">내 주파수</h1>

      <div className="space-y-6">
        <h2 className="text-lg font-semibold">오늘의 주파수</h2>
        <div className="grid grid-cols-1 gap-4">
          {todayFrequencies.length > 0 ? (
            todayFrequencies.map((frequency) => (
              <FrequencyCard key={frequency.frequency_id} frequency={frequency} />
            ))
          ) : (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                오늘의 주파수가 아직 준비되지 않았습니다. 잠시 후 다시 확인해주세요.
              </AlertDescription>
            </Alert>
          )}
        </div>
      </div>

      {(historyFrequencies.length > 0 || historyLoading) && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">주파수 히스토리</h2>
          {historyLoading ? (
            <div className="flex justify-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <FrequencyHistory frequencies={historyFrequencies} />
          )}
        </div>
      )}
    </div>
  )
}
