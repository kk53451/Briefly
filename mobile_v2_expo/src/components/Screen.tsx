import type { ReactNode } from 'react';
import { View, type ViewStyle } from 'react-native';
import { SafeAreaView, type Edge } from 'react-native-safe-area-context';
import { colors } from '@/theme/tokens';

interface Props {
  children: ReactNode;
  background?: string;
  edges?: Edge[];
  style?: ViewStyle;
}

/** Paper-background screen wrapper with safe-area handling. */
export function Screen({
  children,
  background = colors.paper,
  edges = ['top'],
  style,
}: Props) {
  return (
    <SafeAreaView
      edges={edges}
      style={{ flex: 1, backgroundColor: background }}
    >
      <View style={[{ flex: 1 }, style]}>{children}</View>
    </SafeAreaView>
  );
}
