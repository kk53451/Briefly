"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { apiClient } from "@/lib/api"
import { toast } from "sonner"

const transitionProps = {
  type: "spring",
  stiffness: 500,
  damping: 30,
  mass: 0.5,
}

export default function InterestSelector() {
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

  const toggleCategory = (category: string) => {
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
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen container max-w-2xl mx-auto p-6 pt-20">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="text-3xl text-center">환영합니다!</CardTitle>
          <CardDescription className="text-center text-base">
            관심 있는 뉴스 카테고리를 선택해주세요.
            <br />
            매일 아침 선택한 카테고리의 뉴스 요약을 받아보실 수 있습니다.
          </CardDescription>
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
        <CardFooter className="flex justify-center">
          <Button
            onClick={handleComplete}
            disabled={selectedCategories.length === 0 || submitting}
            className="px-8 py-6 rounded-full"
            size="lg"
          >
            {submitting ? "처리 중..." : "시작하기"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
