import { View, Text, type DimensionValue } from 'react-native';
import { Image } from 'expo-image';
import { colors, fontFamily, radius } from '@/theme/tokens';
import { getCategory } from '@/theme/categories';

interface Props {
  uri?: string | null;
  width?: DimensionValue;
  height?: number;
  label?: string;
  categoryId?: string;
  borderRadius?: number;
}

/**
 * Editorial image slot.
 * Shows real image when `uri` is valid, otherwise a striped, category-tinted placeholder.
 */
export function Placeholder({
  uri,
  width = '100%',
  height = 160,
  label = 'photo',
  categoryId = 'economy',
  borderRadius = radius.sm,
}: Props) {
  const tint = getCategory(categoryId)?.color ?? '#8a7b65';

  if (uri) {
    return (
      <Image
        source={{ uri }}
        style={{ width, height, borderRadius, backgroundColor: colors.paper2 }}
        contentFit="cover"
        transition={150}
      />
    );
  }

  return (
    <View
      style={{
        width,
        height,
        borderRadius,
        backgroundColor: `${tint}18`,
        borderWidth: 1,
        borderColor: `${tint}33`,
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      <Text
        style={{
          fontFamily: fontFamily.mono,
          fontSize: 10,
          color: tint,
          letterSpacing: 1.2,
          opacity: 0.8,
          textTransform: 'uppercase',
        }}
      >
        {label}
      </Text>
    </View>
  );
}
