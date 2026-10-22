import { Text, type TextProps, type TextStyle } from 'react-native';
import { colors, fontFamily, fontSize } from '@/theme/tokens';

type Variant =
  | 'display'        // 32px serif 900
  | 'h1'             // 26px serif 800
  | 'h2'             // 22px serif 800
  | 'h3'             // 18px serif 700
  | 'bodySerif'      // 15.5px serif 400, reading
  | 'body'           // 14px sans
  | 'meta'           // 11–12px sans ink-3
  | 'mono'           // 10–11px mono uppercase tracked
  | 'label';         // 10px sans uppercase tracked

interface Props extends TextProps {
  variant?: Variant;
  color?: string;
  italic?: boolean;
  weight?: '400' | '500' | '600' | '700' | '900';
}

const BASE: Record<Variant, TextStyle> = {
  display:   { fontFamily: fontFamily.serifBlack, fontSize: fontSize.xxxl, color: colors.ink, letterSpacing: -1 },
  h1:        { fontFamily: fontFamily.serifBlack, fontSize: 26,             color: colors.ink, letterSpacing: -0.5 },
  h2:        { fontFamily: fontFamily.serif,      fontSize: fontSize.xxl,   color: colors.ink, letterSpacing: -0.4 },
  h3:        { fontFamily: fontFamily.serif,      fontSize: fontSize.lg,    color: colors.ink, letterSpacing: -0.3 },
  bodySerif: { fontFamily: fontFamily.serifRegular, fontSize: 15.5,         color: colors.ink, lineHeight: 26 },
  body:      {                                    fontSize: fontSize.sm,    color: colors.ink2, lineHeight: 22 },
  meta:      {                                    fontSize: fontSize.xs,    color: colors.ink3 },
  mono:      { fontFamily: fontFamily.mono,       fontSize: fontSize.xxs,   color: colors.ink3, letterSpacing: 1.4 },
  label:     {                                    fontSize: fontSize.xxs,   color: colors.ink3, letterSpacing: 1.4 },
};

export function AppText({
  variant = 'body',
  color,
  italic,
  weight,
  style,
  ...rest
}: Props) {
  return (
    <Text
      {...rest}
      style={[
        BASE[variant],
        color ? { color } : null,
        italic ? { fontStyle: 'italic' } : null,
        weight ? { fontWeight: weight } : null,
        style,
      ]}
    />
  );
}
