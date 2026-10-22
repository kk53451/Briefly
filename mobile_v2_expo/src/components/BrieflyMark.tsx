import { Text, View, type StyleProp, type ViewStyle } from 'react-native';
import { colors, fontFamily } from '@/theme/tokens';

interface Props {
  size?: number;
  color?: string;
  dotColor?: string;
  style?: StyleProp<ViewStyle>;
}

/** "Briefly." masthead wordmark. Serif 700 + rust accent dot. */
export function BrieflyMark({
  size = 18,
  color = colors.ink,
  dotColor = colors.accent,
  style,
}: Props) {
  return (
    <View style={style}>
      <Text
        style={{
          fontFamily: fontFamily.serif,
          fontSize: size,
          color,
          letterSpacing: -size * 0.02,
        }}
      >
        Briefly
        <Text style={{ color: dotColor }}>.</Text>
      </Text>
    </View>
  );
}
