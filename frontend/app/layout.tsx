import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { SonnerProvider } from "@/components/sonner-provider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Briefly - AI 기반 뉴스 오디오 서비스",
  description: "최신 뉴스를 요약하고 음성으로 제공하는 AI 기반 뉴스 오디오 서비스",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
          <SonnerProvider />
        </ThemeProvider>
      </body>
    </html>
  )
}
