"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Play, Pause, Volume2, VolumeX } from "lucide-react"
import { cn } from "@/lib/utils"

interface AudioPlayerProps {
  audioUrl: string
  title?: string
  onEnded?: () => void
  onError?: () => void
  className?: string
  compact?: boolean
}

export function AudioPlayer({ audioUrl, title, onEnded, onError, className, compact = false }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isMuted, setIsMuted] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (audioRef.current) {
        audioRef.current.pause()
      }
    }
  }, [])

  useEffect(() => {
    // Reset state when audio URL changes
    setIsPlaying(false)
    setCurrentTime(0)
    setDuration(0)
    setIsLoading(true)
    setError(null)
  }, [audioUrl])

  const togglePlay = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
    } else {
      const playPromise = audioRef.current.play()
      if (playPromise !== undefined) {
        playPromise.catch((error) => {
          console.error("Audio playback failed:", error)
          setError("Failed to play audio")
          if (onError) onError()
        })
      }
    }
    setIsPlaying(!isPlaying)
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration)
      setIsLoading(false)
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
    if (onEnded) onEnded()
  }

  const handleAudioError = () => {
    setError("Could not load audio file")
    setIsLoading(false)
    if (onError) onError()
  }

  const toggleMute = () => {
    if (audioRef.current) {
      const newMuteState = !isMuted
      audioRef.current.muted = newMuteState
      setIsMuted(newMuteState)
    }
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, "0")}`
  }

  return (
    <div className={cn("flex flex-col space-y-2 w-full", className)}>
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={handleAudioError}
        preload="metadata"
      />

      {title && <h3 className="text-sm font-medium">{title}</h3>}

      <div className="flex items-center space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={togglePlay}
          disabled={isLoading || !!error}
          className="h-8 w-8 p-0"
        >
          {isLoading ? (
            <div className="h-4 w-4 animate-spin rounded-full border-b-2 border-primary" />
          ) : isPlaying ? (
            <Pause className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
        </Button>

        <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-primary"
            style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
          />
        </div>

        <Button variant="ghost" size="sm" onClick={toggleMute} disabled={isLoading || !!error} className="h-8 w-8 p-0">
          {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
        </Button>

        <span className="text-xs text-muted-foreground w-16 text-right">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}
