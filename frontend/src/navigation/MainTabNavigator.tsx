import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from 'react-native-paper';
import { MainTabParamList } from './types';
import { Dimensions } from '../lib/theme';

// Placeholder screens (will be implemented)
import HomeScreen from '../screens/home/HomeScreen';
import TodayScreen from '../screens/today/TodayScreen';
import FrequencyScreen from '../screens/frequency/FrequencyScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();

type TabIconName = keyof typeof Ionicons.glyphMap;

interface TabConfig {
  name: keyof MainTabParamList;
  label: string;
  icon: TabIconName;
  activeIcon: TabIconName;
}

const tabs: TabConfig[] = [
  {
    name: 'Home',
    label: '홈',
    icon: 'home-outline',
    activeIcon: 'home',
  },
  {
    name: 'Today',
    label: '투데이',
    icon: 'today-outline',
    activeIcon: 'today',
  },
  {
    name: 'Frequency',
    label: '프리퀀시',
    icon: 'headset-outline',
    activeIcon: 'headset',
  },
  {
    name: 'Profile',
    label: '프로필',
    icon: 'person-outline',
    activeIcon: 'person',
  },
];

export default function MainTabNavigator() {
  const theme = useTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textTertiary,
        tabBarStyle: {
          backgroundColor: theme.colors.background,
          borderTopColor: theme.colors.outline,
          borderTopWidth: 1,
          height: Dimensions.tabBar,
          paddingBottom: 4,
          paddingTop: 4,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontFamily: 'PlusJakartaSans-Medium',
        },
        headerStyle: {
          backgroundColor: theme.colors.background,
          borderBottomColor: theme.colors.outline,
          borderBottomWidth: 1,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTitleStyle: {
          fontFamily: 'Outfit-Bold',
          fontSize: 20,
          color: theme.colors.textPrimary,
        },
        headerTintColor: theme.colors.textPrimary,
      }}
    >
      {tabs.map((tab) => (
        <Tab.Screen
          key={tab.name}
          name={tab.name}
          component={
            tab.name === 'Home'
              ? HomeScreen
              : tab.name === 'Today'
              ? TodayScreen
              : tab.name === 'Frequency'
              ? FrequencyScreen
              : ProfileScreen
          }
          options={{
            title: tab.label,
            tabBarIcon: ({ focused, color, size }) => (
              <Ionicons
                name={focused ? tab.activeIcon : tab.icon}
                size={size}
                color={color}
              />
            ),
          }}
        />
      ))}
    </Tab.Navigator>
  );
}