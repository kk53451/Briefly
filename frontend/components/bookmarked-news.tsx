"use client"

import { NewsCard } from "./news-card"

// 실제 구현에서는 API에서 데이터를 가져오는 로직 필요
const mockBookmarkedNews = [
  {
    id: "2",
    title: "글로벌 경제 불확실성 증가... 중앙은행 금리 동결 결정",
    summary:
      "글로벌 경제의 불확실성이 증가하는 가운데, 중앙은행이 기준금리를 동결하기로 결정했습니다. 이는 인플레이션 압력과 경기 침체 우려를 동시에 고려한 결정으로 분석됩니다.",
    category: "경제",
    audioUrl: "https://example.com/audio/2.mp3",
    isBookmarked: true,
  },
]

export function BookmarkedNews() {
  const handleBookmark = (id: string) => {
    // 북마크 처리 로직 구현 예정
  }

  const handleShare = (id: string) => {
    // 공유 처리 로직 구현 예정
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">북마크</h1>

      {mockBookmarkedNews.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mockBookmarkedNews.map((news) => (
            <NewsCard
              key={news.id}
              id={news.id}
              title={news.title}
              summary={news.summary}
              category={news.category}
              audioUrl={news.audioUrl}
              isBookmarked={news.isBookmarked}
              onBookmark={handleBookmark}
              onShare={handleShare}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-muted-foreground mb-4">북마크한 뉴스가 없습니다.</p>
        </div>
      )}
    </div>
  )
}
