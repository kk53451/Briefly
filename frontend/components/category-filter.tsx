"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface CategoryFilterProps {
  categories: string[]
  onSelect: (category: string) => void
  defaultSelected?: string
}

export function CategoryFilter({ categories, onSelect, defaultSelected = "전체" }: CategoryFilterProps) {
  const [selected, setSelected] = useState<string>(defaultSelected)
  const [showLeftScroll, setShowLeftScroll] = useState(false)
  const [showRightScroll, setShowRightScroll] = useState(false)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  const handleSelect = (category: string) => {
    setSelected(category)
    onSelect(category)

    // 선택된 카테고리로 스크롤
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current
      const categoryElement = container.querySelector(`[data-category="${category}"]`)

      if (categoryElement) {
        const containerRect = container.getBoundingClientRect()
        const elementRect = categoryElement.getBoundingClientRect()

        // 요소가 컨테이너의 왼쪽이나 오른쪽 밖에 있는지 확인
        if (elementRect.left < containerRect.left || elementRect.right > containerRect.right) {
          // 요소가 컨테이너의 중앙에 오도록 스크롤
          const scrollLeft = elementRect.left - containerRect.left - containerRect.width / 2 + elementRect.width / 2
          container.scrollBy({ left: scrollLeft, behavior: "smooth" })
        }
      }
    }
  }

  // 스크롤 버튼 표시 여부 확인
  const checkScrollButtons = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current
      setShowLeftScroll(scrollLeft > 0)
      setShowRightScroll(scrollLeft < scrollWidth - clientWidth - 5) // 5px 여유 추가
    }
  }

  // 스크롤 이벤트 리스너 등록
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (scrollContainer) {
      scrollContainer.addEventListener("scroll", checkScrollButtons)
      // 초기 상태 확인
      checkScrollButtons()

      // 창 크기 변경 시 스크롤 버튼 상태 업데이트
      window.addEventListener("resize", checkScrollButtons)
    }

    return () => {
      if (scrollContainer) {
        scrollContainer.removeEventListener("scroll", checkScrollButtons)
      }
      window.removeEventListener("resize", checkScrollButtons)
    }
  }, [])

  // 스크롤 버튼 클릭 핸들러
  const handleScrollLeft = () => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current
      const scrollAmount = Math.min(container.clientWidth * 0.8, 250)
      container.scrollBy({ left: -scrollAmount, behavior: "smooth" })
    }
  }

  const handleScrollRight = () => {
    if (scrollContainerRef.current) {
      const container = scrollContainerRef.current
      const scrollAmount = Math.min(container.clientWidth * 0.8, 250)
      container.scrollBy({ left: scrollAmount, behavior: "smooth" })
    }
  }

  return (
    <div className="relative w-full mb-6">
      <div className="flex justify-center w-full">
        <div className="relative w-full max-w-full overflow-hidden flex justify-center">
          {/* 왼쪽 스크롤 버튼 */}
          {showLeftScroll && (
            <button
              onClick={handleScrollLeft}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm rounded-full p-2 shadow-sm border border-border touch-manipulation"
              aria-label="이전 카테고리 보기"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          )}

          {/* 카테고리 스크롤 영역 */}
          <div
            ref={scrollContainerRef}
            className="flex space-x-3 py-4 px-4 overflow-x-auto scrollbar-hide snap-x snap-mandatory scroll-smooth mx-auto justify-center touch-pan-x min-h-[60px]"
            style={{ WebkitOverflowScrolling: "touch" }}
          >
            <div className="snap-center" data-category="전체">
              <CategoryButton isSelected={selected === "전체"} onClick={() => handleSelect("전체")} label="전체" />
            </div>
            {categories.map((category) => (
              <div key={category} className="snap-center" data-category={category}>
                <CategoryButton
                  isSelected={selected === category}
                  onClick={() => handleSelect(category)}
                  label={category}
                />
              </div>
            ))}
          </div>

          {/* 오른쪽 스크롤 버튼 */}
          {showRightScroll && (
            <button
              onClick={handleScrollRight}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm rounded-full p-2 shadow-sm border border-border touch-manipulation"
              aria-label="다음 카테고리 보기"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

interface CategoryButtonProps {
  isSelected: boolean
  onClick: () => void
  label: string
}

function CategoryButton({ isSelected, onClick, label }: CategoryButtonProps) {
  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={onClick}
        className={cn(
          "px-4 py-2.5 rounded-full transition-all duration-300 font-medium whitespace-nowrap min-w-[70px] touch-manipulation relative",
          isSelected
            ? "text-primary-foreground bg-primary hover:bg-primary/90"
            : "text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/90",
        )}
      >
        {label}
        {isSelected && (
          <motion.div
            layoutId="activeCategoryIndicator"
            className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-full"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
          />
        )}
      </Button>
    </div>
  )
}
