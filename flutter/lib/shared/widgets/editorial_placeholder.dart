import 'package:flutter/material.dart';

import '../../core/constants/categories.dart';
import '../../core/theme/app_theme.dart';

/// 프로토타입 `<Placeholder>` 포팅 — 이미지 없을 때 사선 스트라이프 패턴.
class EditorialPlaceholder extends StatelessWidget {
  final double width;
  final double height;
  final String? label;
  final Category cat;
  final double radius;

  const EditorialPlaceholder({
    super.key,
    this.width = double.infinity,
    this.height = 160,
    this.label,
    required this.cat,
    this.radius = AppRadius.sm,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: cat.color.withValues(alpha: 0.2)),
      ),
      foregroundDecoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: _stripePattern(cat.color),
      ),
      child: Center(
        child: Text(
          (label ?? 'photo').toUpperCase(),
          style: TextStyle(
            fontFamily: AppFonts.mono,
            fontSize: 12,
            letterSpacing: 0.96,
            color: cat.color.withValues(alpha: 0.8),
          ),
        ),
      ),
    );
  }

  /// repeating-linear-gradient(135deg, c22 0 8px, c11 8px 16px) 근사.
  LinearGradient _stripePattern(Color c) {
    return LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [
        c.withValues(alpha: 0.13),
        c.withValues(alpha: 0.13),
        c.withValues(alpha: 0.07),
        c.withValues(alpha: 0.07),
      ],
      stops: const [0, 0.5, 0.5, 1],
      tileMode: TileMode.repeated,
    );
  }
}
