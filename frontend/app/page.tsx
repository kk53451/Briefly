import { Suspense } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { MyFrequency } from "@/components/my-frequency"
import { BookmarkedNews } from "@/components/bookmarked-news"
import { History } from "@/components/history"
import { UserProfile } from "@/components/user-profile"
import { PageHeader } from "@/components/page-header"
import { Loading } from "@/components/loading"
import { RankingNews } from "@/components/ranking-news"
import { redirect } from "next/navigation"

export default function HomePage() {
  // 기본 페이지는 랭킹 페이지로 리다이렉트
  redirect("/ranking")

  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />
      <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
        <Tabs defaultValue="ranking" className="w-full">
          <TabsList className="grid grid-cols-5 mb-8">
            <TabsTrigger value="ranking">랭킹</TabsTrigger>
            <TabsTrigger value="today">오늘의 뉴스</TabsTrigger>
            <TabsTrigger value="frequency">내 주파수</TabsTrigger>
            <TabsTrigger value="bookmarks">북마크</TabsTrigger>
            <TabsTrigger value="profile">프로필</TabsTrigger>
          </TabsList>
          <TabsContent value="ranking">
            <Suspense fallback={<Loading />}>
              <RankingNews />
            </Suspense>
          </TabsContent>
          <TabsContent value="today">
            <Suspense fallback={<Loading />}>
              <div>오늘의 뉴스는 /today 페이지를 이용해주세요.</div>
            </Suspense>
          </TabsContent>
          <TabsContent value="frequency">
            <Suspense fallback={<Loading />}>
              <MyFrequency />
            </Suspense>
          </TabsContent>
          <TabsContent value="bookmarks">
            <Suspense fallback={<Loading />}>
              <BookmarkedNews />
            </Suspense>
          </TabsContent>
          <TabsContent value="history">
            <Suspense fallback={<Loading />}>
              <History />
            </Suspense>
          </TabsContent>
          <TabsContent value="profile">
            <Suspense fallback={<Loading />}>
              <UserProfile />
            </Suspense>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
