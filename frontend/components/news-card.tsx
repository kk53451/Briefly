"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Bookmark, ExternalLink, Share2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatDate } from "@/lib/utils"

interface NewsCardProps {
  id: string
  title: string
  title_ko?: string
  summary: string
  summary_ko?: string
  category: string
  audioUrl?: string
  imageUrl?: string
  publisher?: string
  author?: string
  publishedAt?: string
  isBookmarked?: boolean
  onBookmark?: (id: string) => void
  onRemoveBookmark?: (id: string) => void
  onClick?: () => void
  onShare?: (id: string) => void
}

export function NewsCard({
  id,
  title,
  title_ko,
  summary,
  summary_ko,
  category,
  audioUrl,
  imageUrl,
  publisher,
  author,
  publishedAt,
  isBookmarked = false,
  onBookmark,
  onRemoveBookmark,
  onClick,
  onShare,
}: NewsCardProps) {
  const [bookmarked, setBookmarked] = useState(isBookmarked)

  // 안전한 속성 접근을 위한 기본값 처리
  const safeTitle = title_ko || title || "제목 없음"
  const safeSummary = summary_ko || summary || "요약 없음"
  const safeCategory = category || "기타"
  const safePublisher = publisher || "출처 미상"

  const toggleBookmark = (e: React.MouseEvent) => {
    e.stopPropagation()
    const newState = !bookmarked
    setBookmarked(newState)

    if (newState) {
      if (onBookmark) onBookmark(id)
    } else {
      if (onRemoveBookmark) onRemoveBookmark(id)
    }
  }

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onShare) onShare(id)

    // 네이티브 공유 API 사용
    if (navigator.share) {
      navigator
        .share({
          title: safeTitle,
          text: safeSummary,
          url: `${window.location.origin}/news/${id}`,
        })
        .catch((err) => console.error("공유 실패:", err))
    }
  }

  return (
    <Card className="w-full cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <CardHeader className="pb-1 p-3">
        {imageUrl && (
          <div className="w-full h-28 overflow-hidden rounded-md mb-2">
            <img src={imageUrl || "/placeholder.svg"} alt={safeTitle} className="w-full h-full object-cover" />
          </div>
        )}
        <div className="flex justify-between items-start">
          <Badge variant="outline" className="mb-1 text-xs">
            {safeCategory}
          </Badge>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleBookmark}
            className={cn("h-6 w-6", bookmarked ? "text-yellow-500" : "text-muted-foreground")}
          >
            <Bookmark className="h-3 w-3" />
            <span className="sr-only">북마크</span>
          </Button>
        </div>
        <CardTitle className="text-lg line-clamp-2">{safeTitle}</CardTitle>
        {(publisher || publishedAt) && (
          <div className="text-xs text-muted-foreground mt-1">
            {safePublisher}
            {author && ` • ${author}`}
            {publishedAt && ` • ${formatDate(publishedAt)}`}
          </div>
        )}
      </CardHeader>
      <CardContent className="pt-0 px-3 pb-2">
        <p className="text-sm text-muted-foreground line-clamp-3">{safeSummary}</p>
      </CardContent>
      <CardFooter className="flex justify-between p-3 pt-0">
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => {
            e.stopPropagation()
            window.open(`/news/${id}`, "_blank")
          }}
          className="h-7 text-xs"
        >
          <ExternalLink className="h-3 w-3 mr-1" />
          자세히
        </Button>
        <Button variant="ghost" size="icon" onClick={handleShare} className="h-7 w-7">
          <Share2 className="h-3 w-3" />
          <span className="sr-only">공유하기</span>
        </Button>
      </CardFooter>
    </Card>
  )
}
