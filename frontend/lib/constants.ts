export const AVAILABLE_CATEGORIES = ["정치", "경제", "사회", "생활/문화", "IT/과학", "연예"]

// 영어 카테고리명을 한국어로 매핑 (DynamoDB 구조에 맞게)
export const CATEGORY_MAP: Record<string, string> = {
  politics: "정치",
  economy: "경제", 
  society: "사회",
  culture: "생활/문화",
  tech: "IT/과학",
  entertainment: "연예",
}

// 한국어를 영어로 매핑 (역방향)
export const REVERSE_CATEGORY_MAP: Record<string, string> = {
  정치: "politics",
  경제: "economy",
  사회: "society",
  "생활/문화": "culture",
  "IT/과학": "tech",
  연예: "entertainment",
}
