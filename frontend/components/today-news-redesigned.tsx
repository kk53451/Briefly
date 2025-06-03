"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { format } from "date-fns"
import { ko } from "date-fns/locale"
import { apiClient } from "@/lib/api"
import { AVAILABLE_CATEGORIES } from "@/lib/constants"
import type { NewsItem } from "@/types/api"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, ChevronLeft, ChevronRight, Info } from "lucide-react"
import { Button } from "@/components/ui/button"
import { showError, showSuccess } from "@/lib/toast"
import { cn } from "@/lib/utils"
import { NewsDetailCard } from "./news-detail-card"
import { ProgressIndicator } from "./progress-indicator"
import { motion, AnimatePresence } from "framer-motion"

export function TodayNewsRedesigned() {
  const router = useRouter()
  const [newsData, setNewsData] = useState<Record<string, NewsItem[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>("")
  const [currentNewsIndex, setCurrentNewsIndex] = useState(0)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [todayDate, setTodayDate] = useState("")
  const [bookmarks, setBookmarks] = useState<string[]>([])
  const [showLeftScroll, setShowLeftScroll] = useState(false)
  const [showRightScroll, setShowRightScroll] = useState(false)
  const [userCategories, setUserCategories] = useState<string[]>([])
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    checkAuthStatus()
    setTodayDate(
      format(new Date(), "M월 d일 브리핑", {
        locale: ko,
      }),
    )
  }, [])

  useEffect(() => {
    if (isLoggedIn) {
      fetchUserCategories()
      fetchTodayNews()
      fetchBookmarks()
    }
  }, [isLoggedIn])

  useEffect(() => {
    setCurrentNewsIndex(0)
  }, [selectedCategory])

  const checkScrollButtons = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current
      setShowLeftScroll(scrollLeft > 0)
      setShowRightScroll(scrollLeft < scrollWidth - clientWidth - 5)
    }
  }

  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", checkScrollButtons)
      checkScrollButtons()
      window.addEventListener("resize", checkScrollButtons)
    }

    return () => {
      if (scrollContainer) {
        scrollContainer.removeEventListener("scroll", checkScrollButtons)
      }
      window.removeEventListener("resize", checkScrollButtons)
    }
  }, [])

  const handleScrollLeft = () => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current
      const scrollAmount = Math.min(container.clientWidth * 0.8, 250)
      container.scrollBy({ left: -scrollAmount, behavior: "smooth" })
    }
  }

  const handleScrollRight = () => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current
      const scrollAmount = Math.min(container.clientWidth * 0.8, 250)
      container.scrollBy({ left: scrollAmount, behavior: "smooth" })
    }
  }

  const checkAuthStatus = () => {
    const token = localStorage.getItem("access_token")
    setIsLoggedIn(!!token)
  }

  const fetchUserCategories = async () => {
    try {
      const response = await apiClient.getUserCategories()
      const interests = response?.interests || []
      setUserCategories(interests)

      if (interests.length > 0 && !selectedCategory) {
        setSelectedCategory(interests[0])
      }
    } catch (error) {
      console.error("사용자 카테고리 조회 실패:", error)
      setUserCategories([])
    }
  }

  const fetchTodayNews = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getTodayNews()
      setNewsData(data)
    } catch (error) {
      console.error("오늘의 뉴스 조회 실패:", error)
      setError(`오늘의 뉴스를 불러오지 못했습니다: ${error instanceof Error ? error.message : String(error)}`)
    } finally {
      setLoading(false)
    }
  }

  const fetchBookmarks = async () => {
    try {
      const bookmarkData = await apiClient.getUserBookmarks()
      setBookmarks(bookmarkData.map((item) => item.news_id))
    } catch (error) {
      console.error("북마크 조회 실패:", error)
    }
  }

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category)

    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current
      const categoryElement = container.querySelector(`[data-category="${category}"]`)

      if (categoryElement) {
        const containerRect = container.getBoundingClientRect()
        const elementRect = categoryElement.getBoundingClientRect()

        if (elementRect.left < containerRect.left || elementRect.right > containerRect.right) {
          const scrollLeft = elementRect.left - containerRect.left - containerRect.width / 2 + elementRect.width / 2
          container.scrollBy({ left: scrollLeft, behavior: "smooth" })
        }
      }
    }
  }

  const handleBookmark = async (newsId: string) => {
    if (!isLoggedIn) {
      showError("로그인 필요", "북마크 기능을 사용하려면 로그인이 필요합니다.")
      return
    }

    try {
      await apiClient.bookmarkNews(newsId)
      setBookmarks((prev) => [...prev, newsId])
      showSuccess("북마크 완료", "뉴스가 북마크에 추가되었습니다.")
    } catch (error) {
      console.error("북마크 실패:", error)
      showError("북마크 실패", "북마크 처리 중 오류가 발생했습니다.")
    }
  }

  const handleRemoveBookmark = async (newsId: string) => {
    try {
      await apiClient.removeBookmark(newsId)
      setBookmarks((prev) => prev.filter((id) => id !== newsId))
      showSuccess("북마크 삭제", "북마크가 삭제되었습니다.")
    } catch (error) {
      console.error("북마크 삭제 실패:", error)
      showError("북마크 삭제 실패", "북마크 삭제 중 오류가 발생했습니다.")
    }
  }

  const handlePrevNews = () => {
    if (currentNewsIndex > 0) {
      setCurrentNewsIndex(currentNewsIndex - 1)
    }
  }

  const handleNextNews = () => {
    const currentCategoryNews = newsData[selectedCategory] || []
    if (currentNewsIndex < currentCategoryNews.length - 1) {
      setCurrentNewsIndex(currentNewsIndex + 1)
    }
  }

  const handleViewDetail = (newsId: string) => {
    router.push(`/news/${newsId}`)
  }

  if (!isLoggedIn) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">오늘의 뉴스</h1>
          <Button variant="ghost" size="icon">
            <Info className="h-5 w-5" />
          </Button>
        </div>

        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>오늘의 뉴스를 이용하려면 로그인이 필요합니다.</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">오늘의 뉴스</h1>
          <Button variant="ghost" size="icon">
            <Info className="h-5 w-5" />
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
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">오늘의 뉴스</h1>
          <Button variant="ghost" size="icon">
            <Info className="h-5 w-5" />
          </Button>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!userCategories || userCategories.length === 0) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.back()} className="p-0 hover:bg-transparent">
            <ChevronLeft className="h-6 w-6 mr-2" />
            <h1 className="text-2xl font-bold">{todayDate}</h1>
          </Button>
          <Button variant="ghost" size="icon">
            <Info className="h-5 w-5" />
          </Button>
        </div>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>관심 있는 뉴스 분야를 먼저 선택해 주세요.</AlertDescription>
        </Alert>
        <Button
          onClick={() => router.push("/profile/categories")}
          className="w-full"
        >
          카테고리 설정하기
        </Button>
      </div>
    )
  }

  const currentCategoryNews = newsData[selectedCategory] || []
  const currentNews = currentCategoryNews[currentNewsIndex]
  const totalNewsCount = currentCategoryNews.length

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-center relative">
        <Button variant="ghost" onClick={() => router.back()} className="absolute left-0 p-0 hover:bg-transparent">
          <ChevronLeft className="h-6 w-6" />
        </Button>
        <h1 className="text-2xl font-bold">{todayDate}</h1>
        <Button variant="ghost" size="icon" className="absolute right-0">
          <Info className="h-5 w-5" />
        </Button>
      </div>

      <div className="relative w-full">
        <div className="flex justify-center w-full">
          <div className="relative w-full max-w-full overflow-hidden flex justify-center">
            {showLeftScroll && (
              <button
                onClick={handleScrollLeft}
                className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm rounded-full p-2 shadow-sm border border-border touch-manipulation"
                aria-label="이전 카테고리 보기"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
            )}

            <div
              ref={scrollContainerRef}
              className="flex space-x-2 py-1 px-2 overflow-x-auto scrollbar-hide snap-x snap-mandatory scroll-smooth mx-auto justify-center touch-pan-x min-h-[40px]"
              style={{ WebkitOverflowScrolling: "touch" }}
            >
              {userCategories.map((category) => (
                <div key={category} className="snap-center" data-category={category}>
                  <div className="relative">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCategorySelect(category)}
                      className={cn(
                        "px-2.5 py-1.5 rounded-full transition-all duration-300 font-medium whitespace-nowrap min-w-[55px] touch-manipulation text-sm",
                        selectedCategory === category
                          ? "text-primary-foreground bg-primary hover:bg-primary/90"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted",
                      )}
                    >
                      {category}
                    </Button>
                    {selectedCategory === category && (
                      <motion.div
                        layoutId="activeCategoryIndicator"
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>

            {showRightScroll && (
              <button
                onClick={handleScrollRight}
                className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm rounded-full p-2 shadow-sm border border-border touch-manipulation"
                aria-label="다음 카테고리 보기"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {totalNewsCount > 0 && (
        <ProgressIndicator currentStep={currentNewsIndex + 1} totalSteps={totalNewsCount} />
      )}

      {totalNewsCount > 0 ? (
        <div className="space-y-2">
          <div className="relative min-h-[400px]">
            <AnimatePresence mode="popLayout">
              <motion.div
                key={currentNews.news_id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ 
                  duration: 0.3,
                  ease: "easeInOut"
                }}
                className="absolute inset-0"
              >
                <NewsDetailCard
                  news={currentNews}
                  isBookmarked={bookmarks.includes(currentNews.news_id)}
                  onBookmark={() => handleBookmark(currentNews.news_id)}
                  onRemoveBookmark={() => handleRemoveBookmark(currentNews.news_id)}
                  onViewDetail={() => handleViewDetail(currentNews.news_id)}
                />
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="flex justify-center space-x-3">
            <Button
              variant="outline"
              size="icon"
              className="rounded-full h-10 w-10 bg-muted"
              onClick={handlePrevNews}
              disabled={currentNewsIndex === 0}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="default"
              size="icon"
              className="rounded-full h-10 w-10 bg-primary"
              onClick={handleNextNews}
              disabled={currentNewsIndex === totalNewsCount - 1}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ) : (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>선택한 카테고리의 뉴스가 없습니다.</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
