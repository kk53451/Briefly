import { PageHeader } from "@/components/page-header"
import { MyFrequency } from "@/components/my-frequency"
import { NavigationTabs } from "@/components/navigation-tabs"

export default function FrequencyPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />
      <NavigationTabs activeTab="frequency" />
      <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
        <MyFrequency />
      </main>
    </div>
  )
}
