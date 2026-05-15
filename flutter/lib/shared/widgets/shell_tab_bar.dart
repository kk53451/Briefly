import 'package:flutter/material.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';

enum ShellTab { home, today, podcast, profile }

extension ShellTabX on ShellTab {
  String get label {
    switch (this) {
      case ShellTab.home:    return '홈';
      case ShellTab.today:   return '투데이';
      case ShellTab.podcast: return '팟캐스트';
      case ShellTab.profile: return '프로필';
    }
  }

  AppIconName get icon {
    switch (this) {
      case ShellTab.home:    return AppIconName.home;
      case ShellTab.today:   return AppIconName.newspaper;
      case ShellTab.podcast: return AppIconName.radio;
      case ShellTab.profile: return AppIconName.person;
    }
  }

  String get route {
    switch (this) {
      case ShellTab.home:    return '/home';
      case ShellTab.today:   return '/today';
      case ShellTab.podcast: return '/podcast';
      case ShellTab.profile: return '/profile';
    }
  }
}

/// 하단 탭바 — 프로토타입 ui.jsx TabBar 포팅.
class ShellTabBar extends StatelessWidget {
  final ShellTab active;
  final ValueChanged<ShellTab> onChanged;

  const ShellTabBar({super.key, required this.active, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.card,
        border: Border(top: BorderSide(color: AppColors.line)),
      ),
      padding: const EdgeInsets.only(top: 8, bottom: 4),
      child: Row(
        children: ShellTab.values.map((t) {
          final isActive = t == active;
          return Expanded(
            child: InkWell(
              onTap: () => onChanged(t),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      appIconData(t.icon),
                      size: 22,
                      color: isActive ? AppColors.ink : AppColors.ink3,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      t.label,
                      style: TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 12,
                        fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
                        letterSpacing: 0.2,
                        color: isActive ? AppColors.ink : AppColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
