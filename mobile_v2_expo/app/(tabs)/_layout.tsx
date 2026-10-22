import { Tabs } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Text, View } from 'react-native';
import { colors, fontFamily } from '@/theme/tokens';

const ICON: Record<string, { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap; label: string }> = {
  home:    { active: 'home',       inactive: 'home-outline',       label: '홈' },
  today:   { active: 'newspaper',  inactive: 'newspaper-outline',  label: '투데이' },
  podcast: { active: 'radio',      inactive: 'radio-outline',      label: '팟캐스트' },
  profile: { active: 'person',     inactive: 'person-outline',     label: '프로필' },
};

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.card,
          borderTopColor: colors.line,
          borderTopWidth: 1,
          height: 64,
          paddingTop: 8,
          paddingBottom: 8,
        },
        tabBarItemStyle: { gap: 4 },
        tabBarLabel: ({ focused }) => {
          const meta = ICON[route.name];
          if (!meta) return null;
          return (
            <Text
              style={{
                fontSize: 10,
                fontFamily: focused ? fontFamily.serif : undefined,
                fontWeight: focused ? '700' : '500',
                color: focused ? colors.ink : colors.ink3,
                letterSpacing: 0.2,
              }}
            >
              {meta.label}
            </Text>
          );
        },
        tabBarIcon: ({ focused }) => {
          const meta = ICON[route.name];
          if (!meta) return null;
          return (
            <View style={{ height: 24, justifyContent: 'center' }}>
              <Ionicons
                name={focused ? meta.active : meta.inactive}
                size={22}
                color={focused ? colors.ink : colors.ink3}
              />
            </View>
          );
        },
      })}
    >
      <Tabs.Screen name="home" />
      <Tabs.Screen name="today" />
      <Tabs.Screen name="podcast" />
      <Tabs.Screen name="profile" />
    </Tabs>
  );
}
