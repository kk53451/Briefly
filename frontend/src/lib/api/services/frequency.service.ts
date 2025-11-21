import { apiClient } from '../client';
import { API_ENDPOINTS } from '../config';
import { Frequency, FrequencyHistory } from '../../../types';

export const frequencyService = {
  // Get user frequencies (today)
  async getUserFrequencies(): Promise<Frequency[]> {
    const response = await apiClient.get<Frequency[]>(
      API_ENDPOINTS.FREQUENCIES.LIST
    );
    return response.data;
  },

  // Get frequency history
  async getFrequencyHistory(): Promise<FrequencyHistory[]> {
    const response = await apiClient.get<FrequencyHistory[]>(
      API_ENDPOINTS.FREQUENCIES.HISTORY
    );
    return response.data;
  },

  // Get frequency by category
  async getFrequencyByCategory(category: string): Promise<Frequency> {
    const response = await apiClient.get<Frequency>(
      API_ENDPOINTS.FREQUENCIES.BY_CATEGORY(category)
    );
    return response.data;
  },
};