"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Calendar, ChevronDown, ChevronUp } from "lucide-react"
import { REVERSE_CATEGORY_MAP, CATEGORY_MAP } from "@/lib/constants"
import type { FrequencyItem } from "@/types/api"
import { formatDate } from "@/lib/utils"
import { AudioPlayer } from "./audio-player"
import { cn } from "@/lib/utils"

interface FrequencyHistoryProps {
  frequencies: FrequencyItem[]
}

export function FrequencyHistory({ frequencies }: FrequencyHistoryProps) {
  const [expandedDate, setExpandedDate] = useState<string | null>(null)
  const [expandedFrequency, setExpandedFrequency] = useState<string | null>(null)

  // Group by date
  const groupByDate = (items: FrequencyItem[]) => {
    const groups: Record<string, FrequencyItem[]> = {}

    items.forEach((item) => {
      const date = item.date.split("T")[0]
      if (!groups[date]) {
        groups[date] = []
      }
      groups[date].push(item)
    })

    return groups
  }

  const groupedFrequencies = groupByDate(frequencies)
  const sortedDates = Object.keys(groupedFrequencies).sort((a, b) => new Date(b).getTime() - new Date(a).getTime())

  const toggleDate = (date: string) => {
    if (expandedDate === date) {
      setExpandedDate(null)
    } else {
      setExpandedDate(date)
    }
  }

  const toggleFrequency = (frequencyId: string) => {
    if (expandedFrequency === frequencyId) {
      setExpandedFrequency(null)
    } else {
      setExpandedFrequency(frequencyId)
    }
  }

  const getCategoryName = (category: string) => {
    return CATEGORY_MAP[category] || category
  }

  return (
    <div className="space-y-4">
      {sortedDates.map((date) => (
        <div key={date} className="space-y-2">
          <Button
            variant="outline"
            className="w-full flex justify-between items-center"
            onClick={() => toggleDate(date)}
          >
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-2" />
              <span>{formatDate(date)}</span>
            </div>
            <div className="flex items-center">
              <Badge>{groupedFrequencies[date].length}개</Badge>
              {expandedDate === date ? (
                <ChevronUp className="h-4 w-4 ml-2" />
              ) : (
                <ChevronDown className="h-4 w-4 ml-2" />
              )}
            </div>
          </Button>

          {expandedDate === date && (
            <div className="grid grid-cols-1 gap-2 pl-4 mt-2">
              {groupedFrequencies[date].map((frequency) => (
                <Card key={frequency.frequency_id} className="w-full">
                  <CardHeader className="py-3 px-4">
                    <div className="flex justify-between items-center">
                      <Badge variant="outline">{getCategoryName(frequency.category)}</Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleFrequency(frequency.frequency_id)}
                        className="h-8 px-2"
                      >
                        {expandedFrequency === frequency.frequency_id ? "접기" : "듣기"}
                        {expandedFrequency === frequency.frequency_id ? (
                          <ChevronUp className="h-3 w-3 ml-1" />
                        ) : (
                          <ChevronDown className="h-3 w-3 ml-1" />
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent
                    className={cn(
                      "py-2 px-4 transition-all duration-300",
                      expandedFrequency === frequency.frequency_id ? "pb-4" : "pb-2",
                    )}
                  >
                    <p className="text-xs text-muted-foreground line-clamp-2">{frequency.script}</p>

                    {expandedFrequency === frequency.frequency_id && (
                      <div className="mt-4">
                        <AudioPlayer audioUrl={frequency.audio_url} compact={true} className="mt-2" />
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
