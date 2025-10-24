import { NavigatorScreenParams } from "@react-navigation/native";

export type RootStackParamList = {
  Auth: undefined;
  Main: NavigatorScreenParams<MainTabParamList>;
  Onboarding: undefined;
  NewsDetail: { newsId: string };
  Categories: undefined;
};

export type MainTabParamList = {
  Today: undefined;
  Ranking: undefined;
  Podcast: undefined;
  Profile: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  KakaoCallback: { code: string };
};
