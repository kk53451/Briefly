/**
 * Navigation type definitions
 */

import { NavigationProp } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';

// Root Stack (Auth flow)
export type RootStackParamList = {
  Login: undefined;
  Onboarding: undefined;
  Main: undefined;
};

// Main Tab Navigator
export type MainTabParamList = {
  Home: undefined;
  Today: undefined;
  Podcast: undefined;
  Profile: undefined;
};

// News Stack (nested in Home/Today tabs)
export type NewsStackParamList = {
  NewsList: undefined;
  NewsDetail: { newsId: string };
  CategoryNews: { category: string; categoryName: string };
};

// Profile Stack
export type ProfileStackParamList = {
  ProfileMain: undefined;
  Bookmarks: undefined;
  CategorySettings: undefined;
  Settings: undefined;
};

// Navigation props for screens
export type RootStackNavigationProp = StackNavigationProp<RootStackParamList>;
export type MainTabNavigationProp = BottomTabNavigationProp<MainTabParamList>;
export type NewsStackNavigationProp = StackNavigationProp<NewsStackParamList>;
export type ProfileStackNavigationProp = StackNavigationProp<ProfileStackParamList>;
