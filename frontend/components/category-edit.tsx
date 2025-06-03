"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api"
import { toast } from "sonner"

export function CategoryEdit() {
  const router = useRouter()
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCategories()
    fetchUserCategories()
  }, [])

  const fetchCategories = async () => {
    try {
      const data = await apiClient.getCategories()
      const categoryList = data?.categories || []
      setCategories(Array.isArray(categoryList) ? categoryList : [])
    } catch (error) {
      console.error("카테고리 조회 실패:", error)
      setError("카테고리 정보를 불러오지 못했습니다.")
      setCategories([])
    }
  }

  const fetchUserCategories = async () => {
    try {
      const response = await apiClient.getUserCategories()
      const interests = response?.interests || []
      setSelectedCategories(Array.isArray(interests) ? interests : [])
    } catch (error) {
      console.error("사용자 카테고리 조회 실패:", error)
      setError("사용자 카테고리 정보를 불러오지 못했습니다.")
      setSelectedCategories([])
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryChange = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category],
    )
  }

  const handleSave = async () => {
    if (!selectedCategories || selectedCategories.length === 0) {
      toast.error("카테고리 선택 필요", {
        description: "최소 1개 이상 선택해 주세요.",
      })
      return
    }

    try {
      setSubmitting(true)
      await apiClient.updateUserCategories(selectedCategories)
      toast.success("저장 완료", {
        description: "카테고리 설정이 저장되었습니다.",
      })
      router.push("/profile")
    } catch (error) {
      console.error("카테고리 저장 실패:", error)
      toast.error("카테고리 저장 실패", {
        description: "카테고리 저장에 실패했습니다. 다시 시도해주세요.",
      })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">카테고리 설정</h1>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">카테고리 설정</h1>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/profile")}>프로필로 돌아가기</Button>
      </div>
    )
  }

  if (!categories || categories.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">카테고리 설정</h1>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>사용 가능한 카테고리가 없습니다.</AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/profile")}>프로필로 돌아가기</Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">카테고리 설정</h1>
        <Button variant="outline" onClick={() => router.push("/profile")}>
          취소
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>관심 카테고리 설정</CardTitle>
          <CardDescription>매일 아침 선택한 카테고리의 뉴스 요약을 받아보세요.</CardDescription>
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
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={() => router.push("/profile")}>
            취소
          </Button>
          <Button onClick={handleSave} disabled={!selectedCategories || selectedCategories.length === 0 || submitting}>
            {submitting ? "저장 중..." : "저장"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
