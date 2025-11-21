import React from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { useTheme } from 'react-native-paper';
import { AuthStackParamList } from './types';

// Auth screens
import LoginScreen from '../screens/auth/LoginScreen';
import OnboardingScreen from '../screens/auth/OnboardingScreen';
import KakaoCallbackScreen from '../screens/auth/KakaoCallbackScreen';

const Stack = createStackNavigator<AuthStackParamList>();

export default function AuthNavigator() {
  const theme = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.background,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: theme.colors.textPrimary,
        headerTitleStyle: {
          fontFamily: 'Outfit-Bold',
          fontSize: 20,
        },
        cardStyle: {
          backgroundColor: theme.colors.background,
        },
      }}
    >
      <Stack.Screen
        name="Login"
        component={LoginScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="Onboarding"
        component={OnboardingScreen}
        options={{
          title: '관심 카테고리 선택',
          headerLeft: () => null, // Prevent going back
        }}
      />
      <Stack.Screen
        name="KakaoCallback"
        component={KakaoCallbackScreen}
        options={{ headerShown: false }}
      />
    </Stack.Navigator>
  );
}