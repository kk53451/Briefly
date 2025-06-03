"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiClient } from "@/lib/api"
import type { TodayNewsResponse, NewsItem } from "@/types/api"
import { CategoryFilter } from "./category-filter"
import { NewsCard } from "./news-card"
import { NewsCarousel } from "./news-carousel"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { showError, showSuccess } from "@/lib/toast"

export function TodayNews() {
  const router = useRouter()
  const [newsData, setNewsData] = useState<TodayNewsResponse>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [userCategories, setUserCategories] = useState<string[]>([])
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  useEffect(() => {
    if (isLoggedIn) {
      fetchUserCategories()
    }
    fetchTodayNews()
  }, [isLoggedIn])

  const checkAuthStatus = () => {
    const token = localStorage.getItem("access_token")
    setIsLoggedIn(!!token)
  }

  const fetchUserCategories = async () => {
    try {
      const response = await apiClient.getUserCategories()
      const interests = response?.interests || []
      setUserCategories(interests)

      if (interests.length > 0) {
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
      setNewsData(data || {})
    } catch (error) {
      console.error("오늘의 뉴스 조회 실패:", error)
      setError("오늘의 뉴스를 불러오지 못했습니다.")
      setNewsData({})
    } finally {
      setLoading(false)
    }
  }

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category)
  }

  const handleBookmark = async (newsId: string) => {
    if (!isLoggedIn) {
      showError("로그인 필요", "북마크 기능을 사용하려면 로그인이 필요합니다.")
      return
    }

    try {
      await apiClient.bookmarkNews(newsId)
      showSuccess("북마크 완료", "뉴스가 북마크에 추가되었습니다.")
    } catch (error) {
      console.error("북마크 실패:", error)
      showError("북마크 실패", "북마크 처리 중 오류가 발생했습니다.")
    }
  }

  const handleRemoveBookmark = async (newsId: string) => {
    try {
      await apiClient.removeBookmark(newsId)
      showSuccess("북마크 삭제", "북마크가 삭제되었습니다.")
    } catch (error) {
      console.error("북마크 삭제 실패:", error)
      showError("북마크 삭제 실패", "북마크 삭제 중 오류가 발생했습니다.")
    }
  }

  const handleCardClick = (newsId: string) => {
    router.push(`/news/${newsId}`)
  }

  if (!isLoggedIn) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">오늘의 뉴스</h1>

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
        <h1 className="text-2xl font-bold">오늘의 뉴스</h1>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">오늘의 뉴스</h1>
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
        <h1 className="text-2xl font-bold">오늘의 뉴스</h1>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>관심 있는 뉴스 분야를 먼저 선택해 주세요.</AlertDescription>
        </Alert>
        <button
          onClick={() => router.push("/profile/categories")}
          className="w-full py-2 px-4 bg-primary text-white rounded-md"
        >
          카테고리 설정하기
        </button>
      </div>
    )
  }

  const selectedCategoryNews = selectedCategory && newsData[selectedCategory] ? newsData[selectedCategory] : []

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">오늘의 뉴스</h1>

      <div className="mb-4">
        <CategoryFilter
          categories={userCategories}
          onSelect={handleCategorySelect}
          defaultSelected={selectedCategory || userCategories[0]}
        />
      </div>

      {selectedCategory && selectedCategoryNews.length > 0 ? (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-4">{selectedCategory} 주요 뉴스</h2>
          <NewsCarousel
            news={selectedCategoryNews}
            onBookmark={handleBookmark}
            onRemoveBookmark={handleRemoveBookmark}
            onCardClick={handleCardClick}
          />
        </div>
      ) : (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>선택한 카테고리의 뉴스가 없습니다.</AlertDescription>
        </Alert>
      )}

      <div>
        <h2 className="text-lg font-semibold mb-4">모든 카테고리</h2>
        {Object.entries(newsData || {}).map(([category, categoryNews]) => {
          if (!categoryNews || !Array.isArray(categoryNews) || categoryNews.length === 0) {
            return null
          }

          return (
            <div key={category} className="mb-8">
              <h3 className="text-md font-medium mb-2">{category}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {categoryNews.slice(0, 2).map((news: NewsItem) => (
                  <NewsCard
                    key={news.news_id}
                    id={news.news_id}
                    title={news.title}
                    title_ko={news.title_ko}
                    summary={news.summary}
                    summary_ko={news.summary_ko}
                    category={category}
                    imageUrl={news.thumbnail_url || news.image_url}
                    publisher={news.publisher}
                    author={news.author}
                    publishedAt={news.published_at}
                    onBookmark={() => handleBookmark(news.news_id)}
                    onRemoveBookmark={() => handleRemoveBookmark(news.news_id)}
                    onClick={() => handleCardClick(news.news_id)}
                    isBookmarked={false}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
