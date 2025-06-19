"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { CategoryFilter } from "./category-filter"
import { NewsCard } from "./news-card"
import { apiClient } from "@/lib/api"
import { AVAILABLE_CATEGORIES } from "@/lib/constants"
import type { NewsItem } from "@/types/api"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { showError, showSuccess } from "@/lib/toast"
import { Button } from "@/components/ui/button"

export function RankingNews() {
  const router = useRouter()
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState("전체")
  const [userCategories, setUserCategories] = useState<string[]>([])
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [bookmarks, setBookmarks] = useState<string[]>([])
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  useEffect(() => {
    if (isLoggedIn) {
      fetchUserCategories()
      fetchBookmarks()
    } else {
      // 로그인하지 않은 경우 전체 뉴스 조회
      fetchNews("전체")
    }
  }, [isLoggedIn])

  useEffect(() => {
    fetchNews(selectedCategory)
  }, [selectedCategory])

  const checkAuthStatus = () => {
    const token = localStorage.getItem("access_token")
    setIsLoggedIn(!!token)
  }

  const fetchUserCategories = async () => {
    try {
      const response = await apiClient.getUserCategories()
      const interests = response?.interests || []
      setUserCategories(interests)

      // 사용자 카테고리가 있어도 기본적으로 "전체"를 유지
      // 사용자가 원한다면 수동으로 변경할 수 있음
    } catch (error) {
      console.error("사용자 카테고리 조회 실패:", error)
      setUserCategories([])
    }
  }

  const fetchBookmarks = async () => {
    try {
      const bookmarkData = await apiClient.getUserBookmarks()
      const bookmarkIds = Array.isArray(bookmarkData) ? bookmarkData.map((item) => item?.news_id).filter(Boolean) : []
      setBookmarks(bookmarkIds)
    } catch (error) {
      console.error("북마크 조회 실패:", error)
      setBookmarks([])
    }
  }

  const fetchNews = async (category: string) => {
    try {
      if (!loading) {
        setIsTransitioning(true)
      }
      setLoading(true)
      setError(null)
      
      const data = await apiClient.getNewsByCategory(category)
      
      setTimeout(() => {
        setNews(Array.isArray(data) ? data : [])
        setIsTransitioning(false)
      }, 200)
      
    } catch (error) {
      console.error("뉴스 조회 실패:", error)
      setError(`뉴스 데이터를 불러오지 못했습니다: ${error instanceof Error ? error.message : String(error)}`)
      setNews([])
      setIsTransitioning(false)
    } finally {
      setTimeout(() => {
        setLoading(false)
      }, 200)
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

  const handleCardClick = (newsId: string) => {
    router.push(`/news/${newsId}`)
  }

  // 랭킹 뉴스는 모든 카테고리를 표시 (사용자 선호 카테고리와 상관없이)
  // CategoryFilter 컴포넌트에서 자동으로 "전체"를 추가하므로 별도로 추가하지 않음
  const availableCategories = AVAILABLE_CATEGORIES

  const displayedNews = showAll ? news : news.slice(0, 10)

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold text-center">오늘의 Top 10 뉴스랭킹</h1>

      <CategoryFilter
        categories={availableCategories}
        onSelect={handleCategorySelect}
        defaultSelected={selectedCategory}
      />

      {loading && news.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="rounded-lg border bg-card p-4 animate-pulse">
              <div className="space-y-2">
                {/* 이미지 스켈레톤 */}
                <div className="w-full h-32 bg-muted rounded-md"></div>
                
                {/* 제목 스켈레톤 */}
                <div className="space-y-1">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-4 bg-muted rounded w-1/2"></div>
                </div>
                
                {/* 요약 스켈레톤 */}
                <div className="space-y-1">
                  <div className="h-3 bg-muted rounded w-full"></div>
                  <div className="h-3 bg-muted rounded w-5/6"></div>
                  <div className="h-3 bg-muted rounded w-2/3"></div>
                </div>
                
                {/* 메타 정보 스켈레톤 */}
                <div className="flex justify-between items-center">
                  <div className="h-3 bg-muted rounded w-1/4"></div>
                  <div className="h-3 bg-muted rounded w-1/6"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <Alert variant="destructive" className="my-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : news.length === 0 ? (
        <Alert className="my-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>선택한 카테고리에 뉴스가 없습니다.</AlertDescription>
        </Alert>
      ) : (
        <div className="space-y-4">
          <div 
            className={`grid grid-cols-1 md:grid-cols-2 gap-3 transition-opacity duration-300 ease-in-out ${
              isTransitioning ? 'opacity-60' : 'opacity-100'
            }`}
          >
            {displayedNews.map((item) => (
              <NewsCard
                key={item.news_id}
                id={item.news_id}
                title={item.title}
                title_ko={item.title_ko}
                summary={item.summary}
                summary_ko={item.summary_ko}
                category={item.category}
                imageUrl={item.thumbnail_url || item.image_url}
                publisher={item.publisher}
                author={item.author}
                publishedAt={item.published_at}
                onBookmark={() => handleBookmark(item.news_id)}
                onRemoveBookmark={() => handleRemoveBookmark(item.news_id)}
                onClick={() => handleCardClick(item.news_id)}
                isBookmarked={bookmarks.includes(item.news_id)}
              />
            ))}
          </div>
          {news.length > 10 && (
            <div className="flex justify-center">
              <Button
                variant="outline"
                onClick={() => setShowAll(!showAll)}
                className="w-full max-w-xs"
              >
                {showAll ? "접기" : "더 보기"}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
