import 'package:flutter/material.dart';

import '../../core/constants/categories.dart';
import '../../core/theme/app_theme.dart';

enum CatBadgeSize { sm, md }

/// 카테고리 pill 라벨: ● <한글명> (대문자 tracking).
class CatBadge extends StatelessWidget {
  final Category cat;
  final CatBadgeSize size;

  const CatBadge({super.key, required this.cat, this.size = CatBadgeSize.sm});

  @override
  Widget build(BuildContext context) {
    final small = size == CatBadgeSize.sm;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: small ? 5 : 7,
          height: small ? 5 : 7,
          decoration: BoxDecoration(color: cat.color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        Text(
          cat.ko,
          style: TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: small ? 10 : 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.6,
            color: cat.color,
          ),
        ),
      ],
    );
  }
}
