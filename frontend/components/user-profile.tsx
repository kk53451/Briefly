"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { apiClient } from "@/lib/api"
import type { UserProfile as UserProfileType, NewsItem } from "@/types/api"
import { NewsCard } from "./news-card"
import { formatDate } from "@/lib/utils"
import { toast } from "sonner"

export function UserProfile() {
  const router = useRouter()
  const [user, setUser] = useState<UserProfileType | null>(null)
  const [bookmarks, setBookmarks] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchUserProfile()
    fetchUserBookmarks()
  }, [])

  const fetchUserProfile = async () => {
    try {
      const userData = await apiClient.getUserProfile()
      setUser(userData)
    } catch (error) {
      console.error("사용자 정보 조회 실패:", error)
      setError("사용자 정보를 불러오지 못했습니다.")
    } finally {
      setLoading(false)
    }
  }

  const fetchUserBookmarks = async () => {
    try {
      const bookmarkData = await apiClient.getUserBookmarks()
      setBookmarks(bookmarkData)
    } catch (error) {
      console.error("북마크 조회 실패:", error)
    }
  }

  const handleCategoryEdit = () => {
    router.push("/profile/categories")
  }

  const handleRemoveBookmark = async (newsId: string) => {
    try {
      await apiClient.removeBookmark(newsId)
      // 북마크 목록 갱신
      setBookmarks(bookmarks.filter((item) => item.news_id !== newsId))
      toast.success("북마크 삭제", {
        description: "북마크가 삭제되었습니다.",
      })
    } catch (error) {
      console.error("북마크 삭제 실패:", error)
      toast.error("북마크 삭제 실패", {
        description: "북마크 삭제 중 오류가 발생했습니다.",
      })
    }
  }

  const handleCardClick = (newsId: string) => {
    router.push(`/news/${newsId}`)
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">프로필</h1>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="space-y-8">
        <h1 className="text-2xl font-bold">프로필</h1>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error || "사용자 정보를 불러오지 못했습니다."}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">프로필</h1>

      <Card>
        <CardHeader className="flex flex-row items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage
              src={user.profile_image || "/placeholder.svg?height=64&width=64&query=user"}
              alt={user.nickname || "사용자"}
            />
            <AvatarFallback>{user.nickname?.[0] || "U"}</AvatarFallback>
          </Avatar>
          <div className="space-y-1">
            <CardTitle>{user.nickname || "익명 사용자"}</CardTitle>
            <CardDescription>{user.user_id || ""}</CardDescription>
            <CardDescription>가입일: {formatDate(user.created_at || "")}</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-2">관심 카테고리</h3>
              <div className="flex flex-wrap gap-2">
                {(user.interests || []).map((category) => (
                  <div key={category} className="bg-muted px-3 py-1 rounded-full text-sm">
                    {category}
                  </div>
                ))}
                {(!user.interests || user.interests.length === 0) && (
                  <div className="text-muted-foreground text-sm">설정된 관심 카테고리가 없습니다.</div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button variant="outline" onClick={handleCategoryEdit}>
            카테고리 설정
          </Button>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>북마크</CardTitle>
          <CardDescription>저장한 뉴스 목록입니다.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="news">
            <TabsList className="mb-4">
              <TabsTrigger value="news">랭킹 뉴스</TabsTrigger>
              <TabsTrigger value="today">오늘의 뉴스</TabsTrigger>
            </TabsList>
            <TabsContent value="news">
              {bookmarks.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {bookmarks.map((news) => (
                    <NewsCard
                      key={news.news_id}
                      id={news.news_id}
                      title={news.title}
                      summary={news.summary}
                      category={news.category}
                      imageUrl={news.thumbnail_url}
                      publisher={news.publisher}
                      publishedAt={news.published_at}
                      isBookmarked={true}
                      onRemoveBookmark={() => handleRemoveBookmark(news.news_id)}
                      onClick={() => handleCardClick(news.news_id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">북마크한 뉴스가 없습니다.</div>
              )}
            </TabsContent>
            <TabsContent value="today">
              {bookmarks.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {bookmarks.map((news) => (
                    <NewsCard
                      key={news.news_id}
                      id={news.news_id}
                      title={news.title}
                      summary={news.summary}
                      category={news.category}
                      imageUrl={news.thumbnail_url}
                      publisher={news.publisher}
                      publishedAt={news.published_at}
                      isBookmarked={true}
                      onRemoveBookmark={() => handleRemoveBookmark(news.news_id)}
                      onClick={() => handleCardClick(news.news_id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">북마크한 오늘의 뉴스가 없습니다.</div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
