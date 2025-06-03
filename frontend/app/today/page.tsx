import { PageHeader } from "@/components/page-header"
import { NavigationTabs } from "@/components/navigation-tabs"
import { TodayNewsRedesigned } from "@/components/today-news-redesigned"

export default function TodayPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />
      <NavigationTabs activeTab="today" />
      <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
        <TodayNewsRedesigned />
      </main>
    </div>
  )
}
