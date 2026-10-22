import { View, Text } from 'react-native';
import { colors, fontFamily } from '@/theme/tokens';
import { getCategory } from '@/theme/categories';

interface Props {
  categoryId: string;
  size?: 'sm' | 'md';
}

/** Tiny category pill: dot + uppercase korean category name, colored per category. */
export function CatBadge({ categoryId, size = 'sm' }: Props) {
  const cat = getCategory(categoryId);
  if (!cat) return null;
  const small = size === 'sm';
  const dotSize = small ? 5 : 7;

  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
      <View
        style={{
          width: dotSize,
          height: dotSize,
          borderRadius: dotSize / 2,
          backgroundColor: cat.color,
        }}
      />
      <Text
        style={{
          fontFamily: fontFamily.monoMedium,
          fontSize: small ? 10 : 12,
          color: cat.color,
          letterSpacing: 0.6,
        }}
      >
        {cat.ko}
      </Text>
    </View>
  );
}
