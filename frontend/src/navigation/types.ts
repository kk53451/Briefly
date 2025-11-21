import { NavigatorScreenParams } from '@react-navigation/native';
import { BottomTabScreenProps } from '@react-navigation/bottom-tabs';
import { StackScreenProps } from '@react-navigation/stack';
import { NewsCard } from '../types';

// Root Stack Navigator
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};

// Auth Stack Navigator
export type AuthStackParamList = {
  Login: undefined;
  Onboarding: undefined;
  KakaoCallback: { code: string };
};

// Main Tab Navigator
export type MainTabParamList = {
  Home: undefined;
  Today: undefined;
  Frequency: undefined;
  Profile: undefined;
};

// Additional Stack Screens (can be accessed from any tab)
export type MainStackParamList = {
  NewsDetail: { news: NewsCard };
  Categories: undefined;
  Bookmarks: undefined;
  FrequencyPlayer: { frequencyId: string };
  Settings: undefined;
};

// Screen Props Types
export type RootStackScreenProps<T extends keyof RootStackParamList> = StackScreenProps<
  RootStackParamList,
  T
>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> = StackScreenProps<
  AuthStackParamList,
  T
>;

export type MainTabScreenProps<T extends keyof MainTabParamList> = BottomTabScreenProps<
  MainTabParamList,
  T
>;

export type MainStackScreenProps<T extends keyof MainStackParamList> = StackScreenProps<
  MainStackParamList,
  T
>;

// Navigation Props for hooks
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}