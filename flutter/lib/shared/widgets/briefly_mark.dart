import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// "Briefly." 워드마크 텍스트. 마침표만 accent 색.
class BrieflyMark extends StatelessWidget {
  final double size;
  final Color? color;

  const BrieflyMark({super.key, this.size = 18, this.color});

  @override
  Widget build(BuildContext context) {
    final ink = color ?? AppColors.ink;
    return Text.rich(
      TextSpan(
        children: [
          TextSpan(text: 'Briefly', style: TextStyle(color: ink)),
          const TextSpan(text: '.', style: TextStyle(color: AppColors.accent)),
        ],
      ),
      style: TextStyle(
        fontFamily: AppFonts.serif,
        fontWeight: FontWeight.w700,
        fontSize: size,
        letterSpacing: -size * 0.02,
        height: 1,
      ),
    );
  }
}
