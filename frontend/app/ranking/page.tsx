import { PageHeader } from "@/components/page-header"
import { RankingNews } from "@/components/ranking-news"
import { NavigationTabs } from "@/components/navigation-tabs"

export default function RankingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />
      <NavigationTabs activeTab="ranking" />
      <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
        <RankingNews />
      </main>
    </div>
  )
}
