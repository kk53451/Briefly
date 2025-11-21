export interface Frequency {
  frequency_id: string; // "politics#2025-01-27"
  category: string; // "politics"
  script: string; // Podcast script (1800-2200 chars)
  audio_url: string; // S3 presigned URL (7-day expiry)
  date: string; // "2025-01-27"
  created_at: string;
}

export interface FrequencyHistory {
  date: string;
  frequencies: Frequency[];
}