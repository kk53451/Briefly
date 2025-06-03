"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { BarChart, Newspaper, Radio, User } from "lucide-react"

interface NavigationTabsProps {
  activeTab?: string
}

export function NavigationTabs({ activeTab }: NavigationTabsProps) {
  const pathname = usePathname()

  const tabs = [
    {
      name: "ranking",
      label: "랭킹",
      href: "/ranking",
      icon: BarChart,
    },
    {
      name: "today",
      label: "오늘의 뉴스",
      href: "/today",
      icon: Newspaper,
    },
    {
      name: "frequency",
      label: "내 주파수",
      href: "/frequency",
      icon: Radio,
    },
    {
      name: "profile",
      label: "프로필",
      href: "/profile",
      icon: User,
    },
  ]

  return (
    <div className="sticky top-16 z-30 w-full border-b bg-background">
      <nav className="container flex h-14 max-w-5xl items-center">
        <div className="flex w-full justify-between">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.name || pathname === tab.href || pathname.startsWith(`${tab.href}/`)
            return (
              <Link
                key={tab.name}
                href={tab.href}
                className={cn(
                  "flex flex-1 flex-col items-center justify-center py-2 text-sm font-medium transition-colors",
                  isActive ? "text-primary" : "text-muted-foreground hover:text-foreground",
                )}
              >
                <tab.icon className="h-5 w-5 mb-1" />
                <span>{tab.label}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
