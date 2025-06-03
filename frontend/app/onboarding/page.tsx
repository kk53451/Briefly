"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { apiClient } from "@/lib/api"
import { toast } from "sonner"

export default function OnboardingPage() {
  const router = useRouter()
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    checkOnboardingStatus()
    fetchCategories()
  }, [])

  const checkOnboardingStatus = async () => {
    try {
      const { onboarded } = await apiClient.getOnboardingStatus()
      if (onboarded) {
        router.push("/ranking")
      }
    } catch (error) {
      console.error("온보딩 상태 확인 실패:", error)
    }
  }

  const fetchCategories = async () => {
    try {
      const data = await apiClient.getCategories()
      setCategories(data.categories)
    } catch (error) {
      console.error("카테고리 조회 실패:", error)
      toast.error("카테고리 조회 실패", {
        description: "카테고리 정보를 불러오지 못했습니다. 다시 시도해주세요.",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryChange = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category],
    )
  }

  const handleComplete = async () => {
    if (selectedCategories.length === 0) {
      toast.error("카테고리 선택 필요", {
        description: "1개 이상의 카테고리를 선택해주세요.",
      })
      return
    }

    try {
      setSubmitting(true)
      await apiClient.updateUserCategories(selectedCategories)
      await apiClient.completeOnboarding()
      router.push("/ranking")
    } catch (error) {
      console.error("온보딩 완료 실패:", error)
      toast.error("서버 저장 실패", {
        description: "서버 저장에 실패했습니다. 다시 시도해주세요.",
      })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">환영합니다!</CardTitle>
          <CardDescription>
            관심 있는 뉴스 카테고리를 선택해주세요. 매일 아침 선택한 카테고리의 뉴스 요약을 받아보실 수 있습니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {categories.map((category) => (
              <div key={category} className="flex items-center space-x-2">
                <Checkbox
                  id={category}
                  checked={selectedCategories.includes(category)}
                  onCheckedChange={() => handleCategoryChange(category)}
                />
                <Label htmlFor={category}>{category}</Label>
              </div>
            ))}
          </div>
        </CardContent>
        <CardFooter>
          <Button onClick={handleComplete} disabled={selectedCategories.length === 0 || submitting} className="w-full">
            {submitting ? "처리 중..." : "시작하기"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
