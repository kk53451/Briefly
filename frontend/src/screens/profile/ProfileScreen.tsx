import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MainTabScreenProps } from '../../navigation/types';
import { useAuthStore } from '../../store/authStore';
import { Typography, Spacing } from '../../lib/theme';

export default function ProfileScreen({ navigation }: MainTabScreenProps<'Profile'>) {
  const theme = useTheme();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.title, { color: theme.colors.textPrimary }]}>
          프로필
        </Text>

        {user && (
          <View style={styles.userInfo}>
            <Text style={[styles.nickname, { color: theme.colors.textPrimary }]}>
              {user.nickname}
            </Text>
            <Text style={[styles.userId, { color: theme.colors.textSecondary }]}>
              {user.user_id}
            </Text>
          </View>
        )}

        <Button
          mode="outlined"
          onPress={handleLogout}
          style={styles.logoutButton}
        >
          로그아웃
        </Button>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: Spacing.lg,
  },
  title: {
    ...Typography.h2,
    marginBottom: Spacing.lg,
  },
  userInfo: {
    marginBottom: Spacing.xl,
  },
  nickname: {
    ...Typography.h3,
    marginBottom: Spacing.xs,
  },
  userId: {
    ...Typography.caption,
  },
  logoutButton: {
    marginTop: Spacing.lg,
  },
});