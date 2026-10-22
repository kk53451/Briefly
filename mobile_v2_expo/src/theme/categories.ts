/**
 * 6 categories (스포츠·지역 제외) — ordered for UI tabs.
 * api_name matches backend_v2_supabase/app/constants/category_map.py.
 * color matches briefly_design/project/data/mock.js (warm editorial palette).
 */

import type { ComponentProps } from 'react';
import type Ionicons from '@expo/vector-icons/Ionicons';

type IoniconName = ComponentProps<typeof Ionicons>['name'];

export type CategoryId =
  | 'politics'
  | 'economy'
  | 'society'
  | 'culture'
  | 'international'
  | 'tech';

export interface Category {
  id: CategoryId;
  ko: string;
  color: string;
  icon: IoniconName;
}

export const CATEGORIES: Category[] = [
  { id: 'politics',      ko: '정치',    color: '#B54A3A', icon: 'business-outline' },
  { id: 'economy',       ko: '경제',    color: '#4A7C59', icon: 'trending-up-outline' },
  { id: 'society',       ko: '사회',    color: '#6B4E8A', icon: 'people-outline' },
  { id: 'culture',       ko: '문화',    color: '#B85A75', icon: 'color-palette-outline' },
  { id: 'international', ko: '국제',    color: '#3D6B8C', icon: 'globe-outline' },
  { id: 'tech',          ko: 'IT/과학', color: '#5A5FB0', icon: 'hardware-chip-outline' },
];

export const CAT_BY_ID: Record<CategoryId, Category> = Object.fromEntries(
  CATEGORIES.map((c) => [c.id, c])
) as Record<CategoryId, Category>;

export function getCategory(id: string | null | undefined): Category | null {
  if (!id) return null;
  return CAT_BY_ID[id as CategoryId] ?? null;
}
