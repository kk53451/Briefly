"use client"

import type React from "react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Bookmark } from "lucide-react"
import type { NewsItem } from "@/types/api"
import { formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"

interface NewsDetailCardProps {
  news: NewsItem
  isBookmarked: boolean
  onBookmark: () => void
  onRemoveBookmark: () => void
  onViewDetail: () => void
}

export function NewsDetailCard({
  news,
  isBookmarked,
  onBookmark,
  onRemoveBookmark,
  onViewDetail,
}: NewsDetailCardProps) {
  const toggleBookmark = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (isBookmarked) {
      onRemoveBookmark()
    } else {
      onBookmark()
    }
  }

  return (
    <Card className="overflow-hidden border-0 shadow-lg h-full">
      <div className="relative w-full h-48 overflow-hidden bg-muted">
        <Image
          src={news.image_url || "/placeholder.svg?height=400&width=600&query=news"}
          alt={news.title}
          fill
          className="object-cover transition-opacity duration-300"
          priority
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />
      </div>
      <CardContent className="p-3 bg-card text-card-foreground flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-2">
          <h2 className="text-xl font-bold leading-tight flex-1 mr-2 text-center">{news.title}</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleBookmark}
            className={cn("flex-shrink-0 h-7 w-7", isBookmarked ? "text-yellow-500" : "text-muted-foreground")}
          >
            <Bookmark className="h-3.5 w-3.5" />
            <span className="sr-only">북마크</span>
          </Button>
        </div>

        <div className="text-xs text-muted-foreground mb-2 text-center">
          {news.publisher} • {formatDate(news.published_at)}
        </div>

        <p className="text-sm mb-3 whitespace-pre-line flex-1 line-clamp-6">{news.summary}</p>

        <Button variant="outline" size="sm" className="w-full mt-auto h-8 text-xs" onClick={onViewDetail}>
          자세히 보기
        </Button>
      </CardContent>
    </Card>
  )
}
