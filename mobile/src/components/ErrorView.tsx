/**
 * Error View Component
 * Displays error messages with retry functionality
 */

import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

interface ErrorViewProps {
  message?: string;
  onRetry?: () => void;
  icon?: 'alert-circle' | 'cloud-offline' | 'bug';
}

export const ErrorView: React.FC<ErrorViewProps> = ({
  message = '데이터를 불러오는데 실패했습니다.',
  onRetry,
  icon = 'alert-circle',
}) => {
  const { colors } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Ionicons name={icon} size={64} color={colors.textSecondary} />

      <Text style={[styles.message, { color: colors.text }]}>{message}</Text>

      {onRetry && (
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: colors.primary }]}
          onPress={onRetry}
          activeOpacity={0.8}
        >
          <Ionicons name="refresh" size={20} color="#FFFFFF" />
          <Text style={styles.retryText}>다시 시도</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: Spacing.xl,
  },
  message: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.medium,
    textAlign: 'center',
    marginTop: Spacing.lg,
    marginBottom: Spacing.xl,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    gap: Spacing.sm,
  },
  retryText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.md,
    fontWeight: Typography.fontWeight.semibold,
  },
});
