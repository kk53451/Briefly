"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api"
import { toast } from "sonner"

const transitionProps = {
  type: "spring",
  stiffness: 500,
  damping: 30,
  mass: 0.5,
}

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

  const toggleCategory = (category: string) => {
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
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">카테고리 설정</h1>
          <Button variant="outline" onClick={() => router.push("/profile")}>
            취소
          </Button>
        </div>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">카테고리 설정</h1>
          <Button variant="outline" onClick={() => router.push("/profile")}>
            취소
          </Button>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
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
          <motion.div 
            className="flex flex-wrap gap-3 overflow-visible" 
            layout 
            transition={transitionProps}
          >
            {categories.map((category) => {
              const isSelected = selectedCategories.includes(category)
              return (
                <motion.button
                  key={category}
                  onClick={() => toggleCategory(category)}
                  layout
                  initial={false}
                  animate={{
                    backgroundColor: isSelected ? "hsl(var(--primary))" : "transparent",
                  }}
                  whileHover={{
                    backgroundColor: isSelected ? "hsl(var(--primary))" : "hsl(var(--muted))",
                  }}
                  whileTap={{
                    scale: 0.95,
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 30,
                    mass: 0.5,
                    backgroundColor: { duration: 0.1 },
                  }}
                  className={`
                    inline-flex items-center px-4 py-2 rounded-full text-base font-medium
                    whitespace-nowrap overflow-hidden border
                    ${
                      isSelected
                        ? "text-primary-foreground border-primary"
                        : "text-foreground/60 border-border hover:text-foreground"
                    }
                  `}
                >
                  <motion.div
                    className="relative flex items-center"
                    animate={{
                      width: isSelected ? "auto" : "100%",
                      paddingRight: isSelected ? "1.5rem" : "0",
                    }}
                    transition={{
                      ease: [0.175, 0.885, 0.32, 1.275],
                      duration: 0.3,
                    }}
                  >
                    <span>{category}</span>
                    <AnimatePresence>
                      {isSelected && (
                        <motion.span
                          initial={{ scale: 0, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          exit={{ scale: 0, opacity: 0 }}
                          transition={{
                            type: "spring",
                            stiffness: 500,
                            damping: 30,
                            mass: 0.5,
                          }}
                          className="absolute right-0"
                        >
                          <div className="w-4 h-4 rounded-full bg-primary-foreground flex items-center justify-center">
                            <Check className="w-3 h-3 text-primary" strokeWidth={1.5} />
                          </div>
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </motion.div>
                </motion.button>
              )
            })}
          </motion.div>
        </CardContent>
        <CardFooter className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => router.push("/profile")}
            disabled={submitting}
          >
            취소
          </Button>
          <Button
            onClick={handleSave}
            disabled={selectedCategories.length === 0 || submitting}
          >
            {submitting ? "저장 중..." : "저장"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
