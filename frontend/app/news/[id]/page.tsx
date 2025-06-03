"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { PageHeader } from "@/components/page-header"
import { NavigationTabs } from "@/components/navigation-tabs"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bookmark, ArrowLeft, ExternalLink } from "lucide-react"
import { apiClient } from "@/lib/api"
import type { NewsDetail } from "@/types/api"
import { formatDate } from "@/lib/utils"

export default function NewsDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [news, setNews] = useState<NewsDetail | null>(null)
  const [isBookmarked, setIsBookmarked] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (params.id) {
      fetchNewsDetail(params.id as string)
    }
  }, [params.id])

  const fetchNewsDetail = async (newsId: string) => {
    try {
      setLoading(true)
      const data = await apiClient.getNewsDetail(newsId)
      setNews(data)

      // 북마크 상태 확인 로직 추가 필요
    } catch (error) {
      console.error("뉴스 상세 조회 실패:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleBookmark = async () => {
    if (!news) return

    try {
      if (isBookmarked) {
        await apiClient.removeBookmark(news.news_id)
      } else {
        await apiClient.bookmarkNews(news.news_id)
      }
      setIsBookmarked(!isBookmarked)
    } catch (error) {
      console.error("북마크 처리 실패:", error)
    }
  }

  const handleBack = () => {
    router.back()
  }

  if (loading) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <PageHeader />
        <NavigationTabs activeTab="ranking" />
        <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </main>
      </div>
    )
  }

  if (!news) {
    return (
      <div className="flex flex-col min-h-screen bg-background">
        <PageHeader />
        <NavigationTabs activeTab="ranking" />
        <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold mb-2">뉴스를 찾을 수 없습니다</h2>
            <Button onClick={handleBack}>뒤로 가기</Button>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />
      <NavigationTabs activeTab="ranking" />
      <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
        <Button variant="ghost" onClick={handleBack} className="mb-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          뒤로 가기
        </Button>

        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-start">
              <Badge variant="outline">{news.category}</Badge>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleBookmark}
                className={isBookmarked ? "text-yellow-500" : "text-muted-foreground"}
              >
                <Bookmark className="h-5 w-5" />
                <span className="sr-only">북마크</span>
              </Button>
            </div>
            <CardTitle className="text-2xl mt-2">{news.title}</CardTitle>
            <div className="text-sm text-muted-foreground mt-2">
              {news.publisher} • {formatDate(news.published_at)}
            </div>
          </CardHeader>
          {news.image_url && (
            <CardContent className="pb-0">
              <img src={news.image_url || "/placeholder.svg"} alt={news.title} className="w-full rounded-md mb-4" />
            </CardContent>
          )}
          <CardContent>
            <div className="prose max-w-none">
              <p className="text-lg font-medium mb-4">{news.summary}</p>
              <div className="whitespace-pre-line">{news.content}</div>
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="outline" className="w-full" onClick={() => window.open(news.content_url, "_blank")}>
              <ExternalLink className="h-4 w-4 mr-2" />
              원문 보기
            </Button>
          </CardFooter>
        </Card>
      </main>
    </div>
  )
}
