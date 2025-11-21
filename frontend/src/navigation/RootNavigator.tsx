import React, { useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer } from '@react-navigation/native';
import { useTheme } from 'react-native-paper';
import { useAuthStore } from '../store/authStore';
import { RootStackParamList } from './types';
import AuthNavigator from './AuthNavigator';
import MainTabNavigator from './MainTabNavigator';

const Stack = createStackNavigator<RootStackParamList>();

// Custom linking configuration for deep links
const linking = {
  prefixes: ['briefly://', 'https://briefly.app'],
  config: {
    screens: {
      Auth: {
        screens: {
          KakaoCallback: 'auth/callback',
        },
      },
      Main: {
        screens: {
          Home: 'home',
          Today: 'today',
          Frequency: 'frequency',
          Profile: 'profile',
        },
      },
    },
  },
};

export default function RootNavigator() {
  const theme = useTheme();
  const { isAuthenticated, isLoading, loadAuth, user } = useAuthStore();

  useEffect(() => {
    loadAuth();
  }, []);

  if (isLoading) {
    // You can return a splash screen component here
    return null;
  }

  return (
    <NavigationContainer
      linking={linking}
      theme={{
        dark: theme.dark,
        colors: {
          primary: theme.colors.primary,
          background: theme.colors.background,
          card: theme.colors.surface,
          text: theme.colors.textPrimary,
          border: theme.colors.outline,
          notification: theme.colors.error,
        },
      }}
    >
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {isAuthenticated && user ? (
          <Stack.Screen name="Main" component={MainTabNavigator} />
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}