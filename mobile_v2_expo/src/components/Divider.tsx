import { View } from 'react-native';
import { colors } from '@/theme/tokens';

interface Props {
  thick?: boolean;
  soft?: boolean;
  color?: string;
  marginVertical?: number;
}

export function Divider({ thick, soft, color, marginVertical = 0 }: Props) {
  return (
    <View
      style={{
        height: thick ? 2 : 1,
        backgroundColor: color ?? (thick ? colors.ink : soft ? colors.lineSoft : colors.line),
        marginVertical,
      }}
    />
  );
}
