import { PageHeader } from "@/components/page-header"
import { UserProfile } from "@/components/user-profile"
import { NavigationTabs } from "@/components/navigation-tabs"

export default function ProfilePage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <PageHeader />
      <NavigationTabs activeTab="profile" />
      <main className="flex-1 container max-w-5xl mx-auto px-4 py-6">
        <UserProfile />
      </main>
    </div>
  )
}
