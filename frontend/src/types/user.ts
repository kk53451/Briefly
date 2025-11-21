export interface User {
  user_id: string; // "kakao_{id}"
  nickname: string;
  profile_image: string;
  interests: string[]; // ["정치", "경제", ...]
  onboarding_completed: boolean;
  created_at: string;
  default_length?: number;
}

export interface AuthResponse {
  access_token: string;
  user_id: string;
  nickname: string;
  profile_image: string;
  onboarding_completed: boolean;
}

export interface UpdateProfileRequest {
  nickname?: string;
  interests?: string[];
  default_length?: number;
}

export interface OnboardingRequest {
  interests: string[];
}