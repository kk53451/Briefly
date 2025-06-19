"use client"

import { NewsCard } from "./news-card"

// 실제 구현에서는 API에서 데이터를 가져오는 로직 필요
const mockHistoryNews = [
  {
    id: "1",
    title: "정부, 디지털 혁신 정책 발표... AI 산업 육성에 5조원 투자",
    summary:
      "정부가 디지털 혁신 정책을 발표했습니다. 이번 정책은 AI 산업 육성에 중점을 두고 있으며, 향후 5년간 5조원을 투자할 계획입니다. 전문가들은 이번 정책이 국내 AI 산업 발전에 큰 도움이 될 것으로 전망하고 있습니다.",
    category: "정치",
    audioUrl: "https://example.com/audio/1.mp3",
    isBookmarked: false,
    listenedAt: "2023-05-22T09:30:00",
  },
  {
    id: "3",
    title: "새로운 AI 기술 개발... 자연어 처리 능력 인간 수준 도달",
    summary:
      "최근 개발된 AI 기술이 자연어 처리 능력에서 인간 수준에 도달했다는 연구 결과가 발표되었습니다. 이 기술은 다양한 산업 분야에 적용될 것으로 기대됩니다.",
    category: "IT/과학",
    audioUrl: "https://example.com/audio/3.mp3",
    isBookmarked: false,
    listenedAt: "2023-05-21T18:15:00",
  },
]

export function History() {
  const handleBookmark = (id: string) => {
    // 북마크 처리 로직 구현 예정
  }

  const handleShare = (id: string) => {
    // 공유 처리 로직 구현 예정
  }

  // 날짜별로 그룹화
  const groupByDate = (news: any[]) => {
    const groups: Record<string, any[]> = {}

    news.forEach((item) => {
      const date = new Date(item.listenedAt).toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })

      if (!groups[date]) {
        groups[date] = []
      }

      groups[date].push(item)
    })

    return groups
  }

  const groupedNews = groupByDate(mockHistoryNews)

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold">히스토리</h1>

      {Object.keys(groupedNews).length > 0 ? (
        Object.entries(groupedNews).map(([date, news]) => (
          <div key={date} className="space-y-4">
            <h2 className="text-lg font-semibold">{date}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {news.map((item) => (
                <NewsCard
                  key={item.id}
                  id={item.id}
                  title={item.title}
                  summary={item.summary}
                  category={item.category}
                  audioUrl={item.audioUrl}
                  isBookmarked={item.isBookmarked}
                  onBookmark={handleBookmark}
                  onShare={handleShare}
                />
              ))}
            </div>
          </div>
        ))
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-muted-foreground mb-4">청취 기록이 없습니다.</p>
        </div>
      )}
    </div>
  )
}
