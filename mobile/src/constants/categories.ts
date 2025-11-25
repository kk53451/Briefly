/**
 * Category definitions for news and podcasts
 * Matches backend category mapping
 */

import { ComponentProps } from 'react';
import { Ionicons } from '@expo/vector-icons';

// Type-safe Ionicons name
export type IconName = ComponentProps<typeof Ionicons>['name'];

export interface Category {
  id: string;          // English API name
  name: string;        // Korean display name
  icon: IconName;      // Icon name from Ionicons (type-safe)
  color: string;       // Accent color for this category
}

export const CATEGORIES: Category[] = [
  {
    id: 'politics',
    name: '정치',
    icon: 'business',
    color: '#EF4444', // Red
  },
  {
    id: 'economy',
    name: '경제',
    icon: 'trending-up',
    color: '#10B981', // Green
  },
  {
    id: 'society',
    name: '사회',
    icon: 'people',
    color: '#8B5CF6', // Purple
  },
  {
    id: 'culture',
    name: '문화',
    icon: 'color-palette',
    color: '#EC4899', // Pink
  },
  {
    id: 'international',
    name: '국제',
    icon: 'globe',
    color: '#3B82F6', // Blue
  },
  {
    id: 'local',
    name: '지역',
    icon: 'location',
    color: '#F59E0B', // Amber
  },
  {
    id: 'sports',
    name: '스포츠',
    icon: 'trophy',
    color: '#06B6D4', // Cyan
  },
  {
    id: 'tech',
    name: 'IT/과학',
    icon: 'hardware-chip',
    color: '#6366F1', // Indigo
  },
];

export const getCategoryById = (id: string): Category | undefined => {
  return CATEGORIES.find((cat) => cat.id === id);
};

export const getCategoryByName = (name: string): Category | undefined => {
  return CATEGORIES.find((cat) => cat.name === name);
};

export const getCategoryColor = (id: string): string => {
  return getCategoryById(id)?.color || '#94A3B8';
};

export const getCategoryIcon = (id: string): IconName => {
  return (getCategoryById(id)?.icon || 'newspaper') as IconName;
};
