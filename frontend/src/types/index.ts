export * from './user';
export * from './news';
export * from './frequency';

// Category types
export type CategoryKorean = "정치" | "경제" | "사회" | "문화" | "국제" | "지역" | "스포츠" | "IT/과학";
export type CategoryEnglish = "politics" | "economy" | "society" | "culture" | "international" | "local" | "sports" | "tech";

export interface Category {
  korean: CategoryKorean;
  english: CategoryEnglish;
  color: string;
}