/**
 * News Image component with placeholder fallback
 * Temporarily using React Native Image instead of expo-image for compatibility
 */

import React, { useState } from 'react';
import { View, StyleSheet, ViewStyle, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTheme } from '../contexts/ThemeContext';

interface NewsImageProps {
  uri?: string;
  style?: ViewStyle;
  aspectRatio?: number;
}

export const NewsImage: React.FC<NewsImageProps> = ({ uri, style, aspectRatio = 16 / 9 }) => {
  const { colors } = useTheme();
  const [imageError, setImageError] = useState(false);

  if (!uri || imageError) {
    return (
      <View style={[styles.container, { aspectRatio }, style]}>
        <LinearGradient
          colors={[colors.primary, colors.primaryLight]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.placeholder}
        >
          <Ionicons name="image-outline" size={48} color="rgba(255,255,255,0.8)" />
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={[styles.container, { aspectRatio }, style]}>
      <Image
        source={{ uri }}
        style={styles.image}
        resizeMode="cover"
        onError={() => setImageError(true)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    width: '100%',
    overflow: 'hidden',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  placeholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
