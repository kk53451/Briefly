"use client"

import { useState, useRef, useEffect } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { NewsCard } from "./news-card"
import type { NewsItem } from "@/types/api"

interface NewsCarouselProps {
  news: NewsItem[]
  onBookmark?: (id: string) => void
  onRemoveBookmark?: (id: string) => void
  onCardClick?: (id: string) => void
  bookmarks?: string[]
}

export function NewsCarousel({ news, onBookmark, onRemoveBookmark, onCardClick, bookmarks = [] }: NewsCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const carouselRef = useRef<HTMLDivElement>(null)

  // 안전한 배열 처리
  const safeNews = Array.isArray(news) ? news : []

  const scrollToIndex = (index: number) => {
    if (carouselRef.current) {
      const scrollAmount = carouselRef.current.offsetWidth * index
      carouselRef.current.scrollTo({
        left: scrollAmount,
        behavior: "smooth",
      })
    }
  }

  const handleNext = () => {
    if (currentIndex < safeNews.length - 1) {
      setCurrentIndex(currentIndex + 1)
    } else {
      setCurrentIndex(0)
    }
  }

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    } else {
      setCurrentIndex(safeNews.length - 1)
    }
  }

  useEffect(() => {
    scrollToIndex(currentIndex)
  }, [currentIndex])

  if (!safeNews || safeNews.length === 0) {
    return <div className="text-center py-4">뉴스가 없습니다.</div>
  }

  return (
    <div className="relative">
      <div ref={carouselRef} className="flex overflow-x-hidden snap-x snap-mandatory">
        {safeNews.map((item) => (
          <div key={item.news_id} className="min-w-full snap-center px-2">
            <NewsCard
              id={item.news_id}
              title={item.title}
              summary={item.summary}
              category={item.category}
              imageUrl={item.thumbnail_url}
              publisher={item.publisher}
              publishedAt={item.published_at}
              isBookmarked={bookmarks.includes(item.news_id)}
              onBookmark={() => onBookmark && onBookmark(item.news_id)}
              onRemoveBookmark={() => onRemoveBookmark && onRemoveBookmark(item.news_id)}
              onClick={() => onCardClick && onCardClick(item.news_id)}
            />
          </div>
        ))}
      </div>

      {safeNews.length > 1 && (
        <>
          <div className="absolute inset-y-0 left-0 flex items-center">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm"
              onClick={handlePrev}
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="sr-only">이전</span>
            </Button>
          </div>

          <div className="absolute inset-y-0 right-0 flex items-center">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full bg-background/80 backdrop-blur-sm"
              onClick={handleNext}
            >
              <ChevronRight className="h-4 w-4" />
              <span className="sr-only">다음</span>
            </Button>
          </div>

          <div className="flex justify-center mt-4 space-x-1">
            {safeNews.map((_, index) => (
              <Button
                key={index}
                variant="ghost"
                size="icon"
                className={`w-2 h-2 rounded-full p-0 ${currentIndex === index ? "bg-primary" : "bg-muted"}`}
                onClick={() => setCurrentIndex(index)}
              >
                <span className="sr-only">{`슬라이드 ${index + 1}`}</span>
              </Button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
