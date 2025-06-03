"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { REVERSE_CATEGORY_MAP, CATEGORY_MAP } from "@/lib/constants"
import type { FrequencyItem } from "@/types/api"
import { formatDate } from "@/lib/utils"
import { AudioPlayer } from "./audio-player"
import { toast } from "sonner"

interface FrequencyCardProps {
  frequency: FrequencyItem
}

export function FrequencyCard({ frequency }: FrequencyCardProps) {
  const [error, setError] = useState<string | null>(null)

  // 안전한 속성 접근
  if (!frequency) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>주파수 데이터를 불러올 수 없습니다.</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  const handleAudioError = () => {
    setError("오디오 파일을 불러올 수 없습니다.")
    toast.error("오디오 로드 실패", {
      description: "주파수를 수신하는데 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
    })
  }

  const getCategoryName = (category: string) => {
    return CATEGORY_MAP?.[category] || category || "기타"
  }

  const safeCategory = frequency.category || "기타"
  const safeScript = frequency.script || "스크립트가 없습니다."
  const safeDate = frequency.date || new Date().toISOString()
  const safeAudioUrl = frequency.audio_url || ""

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-start">
          <Badge variant="outline">{getCategoryName(safeCategory)}</Badge>
          <span className="text-sm text-muted-foreground">{formatDate(safeDate)}</span>
        </div>
        <CardTitle className="text-lg">오늘의 {getCategoryName(safeCategory)} 뉴스</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm text-muted-foreground max-h-24 overflow-y-auto">{safeScript}</div>

        {frequency.duration && (
          <div className="text-xs text-muted-foreground">
            재생 시간: {Math.floor(frequency.duration / 60)}분 {frequency.duration % 60}초
          </div>
        )}

        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : safeAudioUrl ? (
          <AudioPlayer
            audioUrl={safeAudioUrl}
            title={`${getCategoryName(safeCategory)} 뉴스 오디오`}
            onError={handleAudioError}
          />
        ) : (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>오디오 파일이 없습니다.</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
