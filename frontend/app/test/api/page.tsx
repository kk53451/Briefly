"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, CheckCircle, Copy, ExternalLink } from "lucide-react"
import { toast } from "sonner"

export default function ApiTestPage() {
  const [apiUrl, setApiUrl] = useState(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  const [token, setToken] = useState("")
  const [endpoint, setEndpoint] = useState("/api/news/today")
  const [method, setMethod] = useState("GET")
  const [requestBody, setRequestBody] = useState("")
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [responseTime, setResponseTime] = useState<number | null>(null)
  const [statusCode, setStatusCode] = useState<number | null>(null)

  useEffect(() => {
    // 로컬 스토리지에서 토큰 가져오기
    const savedToken = localStorage.getItem("access_token")
    if (savedToken) {
      setToken(savedToken)
    }
  }, [])

  const publicEndpoints = [
    {
      name: "루트 헬스체크",
      path: "/",
      method: "GET",
      description: "API 서버 상태 확인",
    },
    {
      name: "온보딩 페이지 정보",
      path: "/onboarding",
      method: "GET",
      description: "온보딩 페이지 정보 제공 (인증 불필요)",
    },
    {
      name: "전체 카테고리 목록",
      path: "/api/categories",
      method: "GET",
      description: "사용 가능한 뉴스 카테고리 목록 조회",
    },
    { 
      name: "오늘의 뉴스 그룹핑", 
      path: "/api/news/today", 
      method: "GET", 
      description: "오늘의 뉴스를 카테고리별로 그룹핑하여 반환" 
    },
    {
      name: "카테고리별 뉴스 조회",
      path: "/api/news?category=경제",
      method: "GET",
      description: "특정 카테고리의 뉴스 조회 (정치, 경제, 사회, 생활/문화, IT/과학, 연예, 전체)",
    },
    {
      name: "전체 뉴스 조회",
      path: "/api/news?category=전체",
      method: "GET",
      description: "모든 카테고리 뉴스를 균등하게 섞어서 반환",
    },
    { 
      name: "뉴스 상세 조회", 
      path: "/api/news/news-id-example", 
      method: "GET", 
      description: "개별 뉴스 카드 상세 내용 조회" 
    },
  ]

  const authEndpoints = [
    // 인증 API
    { 
      name: "카카오 로그인 시작", 
      path: "/api/auth/kakao/login", 
      method: "GET", 
      description: "카카오 OAuth 로그인 페이지로 리다이렉트" 
    },
    { 
      name: "내 정보 조회", 
      path: "/api/auth/me", 
      method: "GET", 
      description: "현재 로그인한 사용자 정보 조회" 
    },
    { 
      name: "로그아웃", 
      path: "/api/auth/logout", 
      method: "POST", 
      description: "로그아웃 처리" 
    },
    
    // 사용자 API
    { 
      name: "프로필 조회", 
      path: "/api/user/profile", 
      method: "GET", 
      description: "로그인한 사용자의 프로필 정보 조회" 
    },
    {
      name: "프로필 수정",
      path: "/api/user/profile",
      method: "PUT",
      description: "사용자 프로필 정보 수정 (nickname, default_length, profile_image)",
      body: '{"nickname": "새닉네임", "default_length": 5}',
    },
    { 
      name: "북마크 목록 조회", 
      path: "/api/user/bookmarks", 
      method: "GET", 
      description: "사용자가 북마크한 뉴스 목록 조회" 
    },
    { 
      name: "내 주파수 조회", 
      path: "/api/user/frequencies", 
      method: "GET", 
      description: "사용자의 관심 카테고리별 공유 주파수 요약 조회 (오늘 날짜 기준)" 
    },
    { 
      name: "관심 카테고리 조회", 
      path: "/api/user/categories", 
      method: "GET", 
      description: "사용자의 관심 카테고리 목록 조회" 
    },
    {
      name: "관심 카테고리 수정",
      path: "/api/user/categories",
      method: "PUT",
      description: "사용자의 관심 카테고리 목록 수정",
      body: '{"interests": ["정치", "경제", "IT/과학"]}',
    },
    { 
      name: "온보딩 완료", 
      path: "/api/user/onboarding", 
      method: "POST", 
      description: "온보딩 완료 처리" 
    },
    {
      name: "온보딩 상태 확인",
      path: "/api/user/onboarding/status",
      method: "GET",
      description: "온보딩 완료 여부 확인",
    },
    { 
      name: "온보딩 페이지 정보 (인증)", 
      path: "/api/user/onboarding", 
      method: "GET", 
      description: "온보딩 페이지 정보 제공 (인증 필요)" 
    },


    // 뉴스 API
    {
      name: "뉴스 북마크 추가",
      path: "/api/news/bookmark",
      method: "POST",
      description: "뉴스 북마크 추가",
      body: '{"news_id": "news-id-example"}',
    },
    {
      name: "뉴스 북마크 삭제",
      path: "/api/news/bookmark/news-id-example",
      method: "DELETE",
      description: "뉴스 북마크 삭제",
    },

    // 주파수 API
    { 
      name: "내 주파수 목록", 
      path: "/api/frequencies", 
      method: "GET", 
      description: "사용자의 관심 카테고리별 공유 주파수 목록 (오늘 날짜 기준)" 
    },
    { 
      name: "주파수 히스토리", 
      path: "/api/frequencies/history", 
      method: "GET", 
      description: "사용자의 관심 카테고리별 주파수 히스토리 (과거 데이터)" 
    },
    {
      name: "주파수 히스토리 (제한)",
      path: "/api/frequencies/history?limit=10",
      method: "GET",
      description: "주파수 히스토리 조회 (개수 제한)",
    },
    { 
      name: "카테고리별 주파수 상세", 
      path: "/api/frequencies/정치", 
      method: "GET", 
      description: "특정 카테고리의 주파수 상세 정보 조회" 
    },
  ]

  const handleEndpointSelect = (path: string, selectedMethod = "GET", body?: string) => {
    setEndpoint(path)
    setMethod(selectedMethod)
    if (body) {
      setRequestBody(body)
    } else {
      setRequestBody("")
    }
  }

  const handleTest = async () => {
    setLoading(true)
    setError(null)
    setResponse(null)
    setResponseTime(null)
    setStatusCode(null)

    const startTime = Date.now()

    try {
      const url = `${apiUrl}${endpoint}`
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      }

      if (token) {
        headers["Authorization"] = `Bearer ${token}`
      }

      const requestOptions: RequestInit = {
        method,
        headers,
      }

      if (method !== "GET" && requestBody) {
        requestOptions.body = requestBody
      }

      const response = await fetch(url, requestOptions)
      const endTime = Date.now()
      setResponseTime(endTime - startTime)
      setStatusCode(response.status)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API 오류 (${response.status}): ${errorText}`)
      }

      const data = await response.json()
      setResponse(data)
      toast.success("API 테스트 성공", {
        description: `${response.status} - ${responseTime}ms`,
      })
    } catch (error) {
      console.error("API 테스트 오류:", error)
      const errorMessage = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."
      setError(errorMessage)
      toast.error("API 테스트 실패", {
        description: errorMessage,
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success("클립보드에 복사되었습니다")
  }

  const formatJson = (obj: any) => {
    return JSON.stringify(obj, null, 2)
  }

  return (
    <div className="container max-w-6xl py-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Briefly API 테스트</h1>
          <p className="text-muted-foreground mt-2">
            총 26개 엔드포인트 | 실제 구현된 API만 포함 | 최신 업데이트: 2025-01-27
          </p>
        </div>
        <Button variant="outline" onClick={() => window.open("/", "_blank")}>
          <ExternalLink className="h-4 w-4 mr-2" />
          메인 사이트
        </Button>
      </div>

      <Tabs defaultValue="test" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="test">API 테스트</TabsTrigger>
          <TabsTrigger value="endpoints">엔드포인트 목록</TabsTrigger>
          <TabsTrigger value="settings">설정</TabsTrigger>
        </TabsList>

        <TabsContent value="test">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>요청 설정</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="method">HTTP 메서드</Label>
                  <select
                    id="method"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="DELETE">DELETE</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="endpoint">엔드포인트</Label>
                  <div className="flex gap-2">
                    <Input
                      id="endpoint"
                      value={endpoint}
                      onChange={(e) => setEndpoint(e.target.value)}
                      className="flex-1"
                      placeholder="/api/news/today"
                    />
                    <Button onClick={handleTest} disabled={loading}>
                      {loading ? "테스트 중..." : "테스트"}
                    </Button>
                  </div>
                </div>

                {method !== "GET" && (
                  <div className="space-y-2">
                    <Label htmlFor="requestBody">요청 본문 (JSON)</Label>
                    <textarea
                      id="requestBody"
                      value={requestBody}
                      onChange={(e) => setRequestBody(e.target.value)}
                      className="w-full p-2 border rounded-md h-24 font-mono text-sm"
                      placeholder='{"key": "value"}'
                    />
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <Badge variant={token ? "default" : "secondary"}>{token ? "인증됨" : "인증 안됨"}</Badge>
                  {statusCode && <Badge variant={statusCode < 400 ? "default" : "destructive"}>{statusCode}</Badge>}
                  {responseTime && <Badge variant="outline">{responseTime}ms</Badge>}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>응답 결과</CardTitle>
                  {response && (
                    <Button variant="outline" size="sm" onClick={() => copyToClipboard(formatJson(response))}>
                      <Copy className="h-4 w-4 mr-2" />
                      복사
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {error && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {response && (
                  <Alert className="mb-4">
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>요청이 성공적으로 처리되었습니다.</AlertDescription>
                  </Alert>
                )}

                {response && (
                  <div className="p-4 bg-muted rounded-md overflow-auto max-h-96">
                    <pre className="text-sm">{formatJson(response)}</pre>
                  </div>
                )}

                {!response && !error && !loading && (
                  <div className="text-center py-8 text-muted-foreground">API 테스트 결과가 여기에 표시됩니다.</div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="endpoints">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>공개 엔드포인트 ({publicEndpoints.length}개) - 인증 불필요</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3">
                  {publicEndpoints.map((ep) => (
                    <div key={ep.path} className="flex items-center justify-between p-3 border rounded-md">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline">{ep.method}</Badge>
                          <code className="text-sm">{ep.path}</code>
                        </div>
                        <p className="text-sm text-muted-foreground">{ep.description}</p>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => handleEndpointSelect(ep.path, ep.method)}>
                        테스트
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>인증 필요 엔드포인트 ({authEndpoints.length}개) - JWT 토큰 필수</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3">
                  {authEndpoints.map((ep, index) => (
                    <div
                      key={`${ep.method}-${ep.path}-${index}`}
                      className="flex items-center justify-between p-3 border rounded-md"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline">{ep.method}</Badge>
                          <code className="text-sm">{ep.path}</code>
                        </div>
                        <p className="text-sm text-muted-foreground">{ep.description}</p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEndpointSelect(ep.path, ep.method, ep.body)}
                      >
                        테스트
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>API 설정</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="apiUrl">API 기본 URL</Label>
                <Input
                  id="apiUrl"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                />
                <p className="text-xs text-muted-foreground">
                  현재 설정: {process.env.NEXT_PUBLIC_API_URL || "환경변수 없음"}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="token">인증 토큰</Label>
                <Input
                  id="token"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  type="password"
                  placeholder="Bearer 토큰을 입력하세요"
                />
                <p className="text-xs text-muted-foreground">로그인 후 자동으로 로컬 스토리지에서 토큰을 불러옵니다.</p>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    localStorage.setItem("access_token", token)
                    toast.success("토큰이 저장되었습니다.")
                  }}
                >
                  토큰 저장
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    const savedToken = localStorage.getItem("access_token")
                    if (savedToken) {
                      setToken(savedToken)
                      toast.success("저장된 토큰을 불러왔습니다.")
                    } else {
                      toast.error("저장된 토큰이 없습니다.")
                    }
                  }}
                >
                  토큰 불러오기
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    localStorage.removeItem("access_token")
                    setToken("")
                    toast.success("토큰이 삭제되었습니다.")
                  }}
                >
                  토큰 삭제
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
