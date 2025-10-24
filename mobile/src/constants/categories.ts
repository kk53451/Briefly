export const CATEGORY_MAP: { [key: string]: string } = {
  politics: "정치",
  economy: "경제",
  society: "사회",
  culture: "문화",
  tech: "과학기술",
  sports: "스포츠",
};

export const CATEGORIES = [
  { id: "politics", name: "정치", name_en: "politics", icon: "👔" },
  { id: "economy", name: "경제", name_en: "economy", icon: "💰" },
  { id: "society", name: "사회", name_en: "society", icon: "🏛️" },
  { id: "culture", name: "문화", name_en: "culture", icon: "🎭" },
  { id: "tech", name: "과학기술", name_en: "tech", icon: "💻" },
  { id: "sports", name: "스포츠", name_en: "sports", icon: "⚽" },
];

export const getCategoryName = (categoryId: string): string => {
  return CATEGORY_MAP[categoryId] || categoryId;
};

export const getCategoryIcon = (categoryId: string): string => {
  const category = CATEGORIES.find((c) => c.id === categoryId);
  return category?.icon || "📰";
};
