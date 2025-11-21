import { Category, CategoryKorean, CategoryEnglish } from '../../types';

export const CATEGORIES: Category[] = [
  { korean: "정치", english: "politics", color: "#6366F1" },
  { korean: "경제", english: "economy", color: "#14B8A6" },
  { korean: "사회", english: "society", color: "#F59E0B" },
  { korean: "문화", english: "culture", color: "#F59E0B" },
  { korean: "국제", english: "international", color: "#EC4899" },
  { korean: "지역", english: "local", color: "#10B981" },
  { korean: "스포츠", english: "sports", color: "#84CC16" },
  { korean: "IT/과학", english: "tech", color: "#8B5CF6" },
];

export const CATEGORY_MAP: Record<CategoryKorean, CategoryEnglish> = {
  "정치": "politics",
  "경제": "economy",
  "사회": "society",
  "문화": "culture",
  "국제": "international",
  "지역": "local",
  "스포츠": "sports",
  "IT/과학": "tech",
};

export const CATEGORY_COLOR_MAP: Record<CategoryEnglish, string> = {
  "politics": "#6366F1",
  "economy": "#14B8A6",
  "society": "#F59E0B",
  "culture": "#F59E0B",
  "international": "#EC4899",
  "local": "#10B981",
  "sports": "#84CC16",
  "tech": "#8B5CF6",
};

export const getCategoryColor = (category: CategoryEnglish): string => {
  return CATEGORY_COLOR_MAP[category] || "#3B82F6";
};

export const getCategoryKorean = (category: CategoryEnglish): CategoryKorean | null => {
  const found = CATEGORIES.find(c => c.english === category);
  return found ? found.korean : null;
};

export const getCategoryEnglish = (category: CategoryKorean): CategoryEnglish | null => {
  return CATEGORY_MAP[category] || null;
};