import React, { ReactNode } from "react";
import { View, StyleSheet, ViewProps, TouchableOpacity, TouchableOpacityProps } from "react-native";
import { Colors, Spacing, BorderRadius } from "../constants/theme";

interface CardProps extends ViewProps {
  children: ReactNode;
  variant?: "default" | "flat";
  onPress?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = "default",
  onPress,
  style,
  ...props
}) => {
  const cardStyle = [styles.card, variant === "flat" && styles.flat, style];

  if (onPress) {
    return (
      <TouchableOpacity style={cardStyle} onPress={onPress} activeOpacity={0.7} {...props}>
        {children}
      </TouchableOpacity>
    );
  }

  return (
    <View style={cardStyle} {...props}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.backgroundCard,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  flat: {
    borderWidth: 0,
    elevation: 0,
  },
});
