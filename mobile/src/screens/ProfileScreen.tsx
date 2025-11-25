/**
 * Profile Screen - User profile and settings
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Switch,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/api';
import { CATEGORIES } from '../constants/categories';
import { Spacing, Typography, BorderRadius, Shadows } from '../constants/theme';

export const ProfileScreen: React.FC = () => {
  const navigation = useNavigation();
  const { user, logout } = useAuth();
  const { colors, activeTheme, toggleTheme } = useTheme();
  const [bookmarkCount, setBookmarkCount] = useState(0);

  useEffect(() => {
    loadBookmarkCount();
  }, []);

  const loadBookmarkCount = async () => {
    if (!user) return;
    try {
      const bookmarks = await apiClient.getBookmarks();
      setBookmarkCount(bookmarks.length);
    } catch (error) {
      console.error('Failed to load bookmarks:', error);
    }
  };

  const handleLogout = () => {
    Alert.alert('로그아웃', '정말 로그아웃 하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          await logout();
        },
      },
    ]);
  };

  const userInterests = user?.interests || [];

  // 로그인하지 않은 경우
  if (!user) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.loginPromptContainer}>
          <View style={[styles.loginPromptCard, { backgroundColor: colors.card }]}>
            <Ionicons name="person-circle-outline" size={80} color={colors.primary} />
            <Text style={[styles.loginPromptTitle, { color: colors.text }]}>
              로그인이 필요합니다
            </Text>
            <Text style={[styles.loginPromptSubtitle, { color: colors.textSecondary }]}>
              로그인하고 맞춤형 뉴스를{'\n'}경험해보세요
            </Text>
            <TouchableOpacity
              style={[styles.loginButton, { backgroundColor: colors.primary }]}
              onPress={() => navigation.navigate('Login' as never)}
            >
              <Text style={styles.loginButtonText}>카카오로 로그인</Text>
            </TouchableOpacity>

            {/* 다크모드 토글은 로그인 없이도 사용 가능 */}
            <View style={styles.guestSettings}>
              <TouchableOpacity
                style={[styles.settingItem, { backgroundColor: colors.card }]}
                onPress={toggleTheme}
                activeOpacity={0.7}
              >
                <View style={styles.settingLeft}>
                  <Ionicons
                    name={activeTheme === 'dark' ? 'moon' : 'sunny'}
                    size={24}
                    color={colors.text}
                  />
                  <View style={styles.settingInfo}>
                    <Text style={[styles.settingTitle, { color: colors.text }]}>다크 모드</Text>
                    <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
                      {activeTheme === 'dark' ? '켜짐' : '꺼짐'}
                    </Text>
                  </View>
                </View>
                <Switch
                  value={activeTheme === 'dark'}
                  onValueChange={toggleTheme}
                  trackColor={{ false: colors.border, true: colors.primary }}
                  thumbColor="#FFFFFF"
                />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.headerTitle, { color: colors.text }]}>프로필</Text>
        </View>

        {/* Profile Card */}
        <View style={[styles.profileCard, { backgroundColor: colors.card }, Shadows.md]}>
          <View style={styles.profileHeader}>
            {user?.profile_image ? (
              <Image source={{ uri: user.profile_image }} style={styles.avatar} />
            ) : (
              <View style={[styles.avatarPlaceholder, { backgroundColor: colors.primary }]}>
                <Ionicons name="person" size={40} color="#FFFFFF" />
              </View>
            )}
            <View style={styles.profileInfo}>
              <Text style={[styles.nickname, { color: colors.text }]}>{user?.nickname}</Text>
              <Text style={[styles.userId, { color: colors.textSecondary }]}>
                {user?.user_id}
              </Text>
            </View>
          </View>

          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: colors.primary }]}>
                {userInterests.length}
              </Text>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>관심 카테고리</Text>
            </View>
            <View style={[styles.statDivider, { backgroundColor: colors.border }]} />
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: colors.primary }]}>{bookmarkCount}</Text>
              <Text style={[styles.statLabel, { color: colors.textSecondary }]}>북마크</Text>
            </View>
          </View>
        </View>

        {/* Interests Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionTitle, { color: colors.text }]}>관심 카테고리</Text>
            <TouchableOpacity>
              <Text style={[styles.editButton, { color: colors.primary }]}>편집</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.categoriesGrid}>
            {CATEGORIES.filter((cat) => userInterests.includes(cat.name)).map((category) => (
              <View
                key={category.id}
                style={[
                  styles.categoryChip,
                  { backgroundColor: category.color + '20', borderColor: category.color },
                ]}
              >
                <Ionicons name={category.icon} size={16} color={category.color} />
                <Text style={[styles.categoryChipText, { color: category.color }]}>
                  {category.name}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Settings Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>설정</Text>

          {/* Dark Mode Toggle */}
          <TouchableOpacity
            style={[styles.settingItem, { backgroundColor: colors.card }]}
            onPress={toggleTheme}
            activeOpacity={0.7}
          >
            <View style={styles.settingLeft}>
              <Ionicons
                name={activeTheme === 'dark' ? 'moon' : 'sunny'}
                size={24}
                color={colors.text}
              />
              <View style={styles.settingInfo}>
                <Text style={[styles.settingTitle, { color: colors.text }]}>다크 모드</Text>
                <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
                  {activeTheme === 'dark' ? '켜짐' : '꺼짐'}
                </Text>
              </View>
            </View>
            <Switch
              value={activeTheme === 'dark'}
              onValueChange={toggleTheme}
              trackColor={{ false: colors.border, true: colors.primary }}
              thumbColor="#FFFFFF"
            />
          </TouchableOpacity>

          {/* Bookmarks */}
          <TouchableOpacity
            style={[styles.settingItem, { backgroundColor: colors.card }]}
            activeOpacity={0.7}
          >
            <View style={styles.settingLeft}>
              <Ionicons name="bookmark" size={24} color={colors.text} />
              <View style={styles.settingInfo}>
                <Text style={[styles.settingTitle, { color: colors.text }]}>북마크</Text>
                <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
                  저장한 뉴스 {bookmarkCount}개
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color={colors.textSecondary} />
          </TouchableOpacity>

          {/* Notifications */}
          <TouchableOpacity
            style={[styles.settingItem, { backgroundColor: colors.card }]}
            activeOpacity={0.7}
          >
            <View style={styles.settingLeft}>
              <Ionicons name="notifications" size={24} color={colors.text} />
              <View style={styles.settingInfo}>
                <Text style={[styles.settingTitle, { color: colors.text }]}>알림 설정</Text>
                <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
                  푸시 알림 관리
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color={colors.textSecondary} />
          </TouchableOpacity>

          {/* About */}
          <TouchableOpacity
            style={[styles.settingItem, { backgroundColor: colors.card }]}
            activeOpacity={0.7}
          >
            <View style={styles.settingLeft}>
              <Ionicons name="information-circle" size={24} color={colors.text} />
              <View style={styles.settingInfo}>
                <Text style={[styles.settingTitle, { color: colors.text }]}>앱 정보</Text>
                <Text style={[styles.settingSubtitle, { color: colors.textSecondary }]}>
                  버전 1.0.0
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        {/* Logout Button */}
        <TouchableOpacity
          style={[styles.logoutButton, { backgroundColor: colors.error }]}
          onPress={handleLogout}
          activeOpacity={0.8}
        >
          <Ionicons name="log-out-outline" size={20} color="#FFFFFF" />
          <Text style={styles.logoutButtonText}>로그아웃</Text>
        </TouchableOpacity>

        <View style={{ height: Spacing.xxl }} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  header: {
    marginBottom: Spacing.lg,
  },
  headerTitle: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
  },
  profileCard: {
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.xl,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  avatar: {
    width: 70,
    height: 70,
    borderRadius: BorderRadius.full,
  },
  avatarPlaceholder: {
    width: 70,
    height: 70,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileInfo: {
    marginLeft: Spacing.md,
    flex: 1,
  },
  nickname: {
    fontSize: Typography.fontSize.xl,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: 4,
  },
  userId: {
    fontSize: Typography.fontSize.sm,
  },
  statsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingTop: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: Typography.fontSize.sm,
  },
  statDivider: {
    width: 1,
    height: 40,
  },
  section: {
    marginBottom: Spacing.xl,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.bold,
  },
  editButton: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
  },
  categoriesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
  },
  categoryChipText: {
    marginLeft: Spacing.xs,
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.semibold,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.sm,
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingInfo: {
    marginLeft: Spacing.md,
    flex: 1,
  },
  settingTitle: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
    marginBottom: 2,
  },
  settingSubtitle: {
    fontSize: Typography.fontSize.sm,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    marginTop: Spacing.lg,
  },
  logoutButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
    marginLeft: Spacing.sm,
  },
  // Login Prompt Styles
  loginPromptContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  loginPromptCard: {
    width: '100%',
    padding: Spacing.xxl,
    borderRadius: BorderRadius.xl,
    alignItems: 'center',
  },
  loginPromptTitle: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    marginTop: Spacing.lg,
    marginBottom: Spacing.sm,
  },
  loginPromptSubtitle: {
    fontSize: Typography.fontSize.base,
    textAlign: 'center',
    marginBottom: Spacing.xxl,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.relaxed,
  },
  loginButton: {
    width: '100%',
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  loginButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.semibold,
  },
  guestSettings: {
    width: '100%',
    marginTop: Spacing.lg,
  },
});
