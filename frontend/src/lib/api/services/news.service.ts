import { apiClient } from '../client';
import { API_ENDPOINTS } from '../config';
import {
  NewsCard,
  NewsGroupByProvider,
  NewsGroupByCategory,
  BookmarkRequest,
  BookmarkResponse
} from '../../../types';

export const newsService = {
  // Get news list
  async getNewsList(category?: string): Promise<NewsCard[]> {
    const response = await apiClient.get<NewsCard[]>(
      API_ENDPOINTS.NEWS.LIST,
      category ? { category } : undefined
    );
    return response.data;
  },

  // Get today's news grouped by category
  async getTodayNews(): Promise<NewsGroupByCategory[]> {
    const response = await apiClient.get<NewsGroupByCategory[]>(
      API_ENDPOINTS.NEWS.TODAY
    );
    return response.data;
  },

  // Get home news grouped by provider
  async getHomeNews(): Promise<NewsGroupByProvider[]> {
    const response = await apiClient.get<NewsGroupByProvider[]>(
      API_ENDPOINTS.NEWS.HOME
    );
    return response.data;
  },

  // Get news detail
  async getNewsDetail(newsId: string): Promise<NewsCard> {
    const response = await apiClient.get<NewsCard>(
      API_ENDPOINTS.NEWS.DETAIL(newsId)
    );
    return response.data;
  },

  // Add bookmark
  async addBookmark(newsId: string): Promise<BookmarkResponse> {
    const response = await apiClient.post<BookmarkResponse>(
      API_ENDPOINTS.NEWS.BOOKMARK,
      { news_id: newsId } as BookmarkRequest
    );
    return response.data;
  },

  // Remove bookmark
  async removeBookmark(newsId: string): Promise<{ message: string }> {
    const response = await apiClient.delete<{ message: string }>(
      API_ENDPOINTS.NEWS.UNBOOKMARK(newsId)
    );
    return response.data;
  },
};