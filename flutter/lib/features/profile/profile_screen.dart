import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants/categories.dart';
import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/user_profile.dart';
import '../auth/auth_repository.dart';
import '../auth/guest_mode.dart';
import '../settings/font_settings_controller.dart';
import 'data/profile_repository.dart';

/// 프로필 — 로그인 사용자면 Supabase `profiles` row, 게스트면 가명 UI.
class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncProfile = ref.watch(currentProfileProvider);
    final isGuest = ref.watch(guestModeProvider);

    return Container(
      color: AppColors.paper,
      child: SafeArea(
        bottom: false,
        child: Column(
          children: [
            Expanded(
              child: asyncProfile.when(
                loading: () => const Center(
                  child: SizedBox(
                    width: 22, height: 22,
                    child: CircularProgressIndicator(
                      strokeWidth: 2, color: AppColors.ink,
                    ),
                  ),
                ),
                error: (e, _) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      '프로필을 불러오지 못했어요\n$e',
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 13,
                        color: AppColors.ink3,
                      ),
                    ),
                  ),
                ),
                data: (profile) => _Body(profile: profile, isGuest: isGuest),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Body extends StatelessWidget {
  final UserProfile? profile;
  final bool isGuest;
  const _Body({required this.profile, required this.isGuest});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.zero,
      children: [
        _ProfileCard(profile: profile, isGuest: isGuest),
        const _StatsPanel(),
        _SettingsList(profile: profile),
        const _SignOutButton(),
      ],
    );
  }
}

/// 신문체 통계 — "함께한 일 / 들은 에피소드".
/// 현재는 정적 값 (디자인 합의된 placeholder). 추후 user activity 연동 시 교체.
class _StatsPanel extends StatelessWidget {
  const _StatsPanel();

  @override
  Widget build(BuildContext context) {
    const items = [('38', '함께한 일'), ('108', '들은 에피소드')];
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.line)),
      ),
      child: Row(
        children: [
          for (int i = 0; i < items.length; i++)
            Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
                decoration: BoxDecoration(
                  border: i < items.length - 1
                      ? const Border(
                          right: BorderSide(color: AppColors.lineSoft),
                        )
                      : null,
                ),
                child: Column(
                  children: [
                    Text(
                      items[i].$1,
                      style: const TextStyle(
                        fontFamily: AppFonts.serif,
                        fontSize: 28,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.56,
                        color: AppColors.ink,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      items[i].$2,
                      style: const TextStyle(
                        fontFamily: AppFonts.mono,
                        fontSize: 12,
                        letterSpacing: 0.48,
                        color: AppColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ProfileCard extends StatelessWidget {
  final UserProfile? profile;
  final bool isGuest;
  const _ProfileCard({required this.profile, required this.isGuest});

  @override
  Widget build(BuildContext context) {
    final name = profile?.displayName ?? (isGuest ? '게스트 독자' : '독자');
    final sub = isGuest
        ? '게스트 모드 · 로그인해서 기기 간 동기화하기'
        : _joinedSince(profile?.createdAt);
    final image = profile?.profileImage;
    final initial = profile?.initialChar ?? '독';
    // 게스트 모드면 generic person 아이콘 + 회색 톤 배경. 로그인 사용자는 이니셜 유지.
    final hasImage = image != null && image.isNotEmpty;

    return Container(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 18),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.line)),
      ),
      child: Row(
        children: [
          Container(
            width: 64, height: 64,
            decoration: BoxDecoration(
              color: isGuest ? AppColors.paper2 : AppColors.accentSoft,
              border: Border.all(color: AppColors.line),
              shape: BoxShape.circle,
              image: hasImage
                  ? DecorationImage(
                      image: NetworkImage(image), fit: BoxFit.cover,
                    )
                  : null,
            ),
            child: hasImage
                ? null
                : Center(
                    child: isGuest
                        ? const AppIcon(
                            AppIconName.person,
                            size: 32,
                            color: AppColors.ink3,
                          )
                        : Text(
                            initial,
                            style: const TextStyle(
                              fontFamily: AppFonts.serif,
                              fontSize: 26,
                              fontWeight: FontWeight.w900,
                              color: AppColors.accent,
                            ),
                          ),
                  ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 4),
                Text(
                  sub,
                  style: const TextStyle(
                    fontFamily: AppFonts.mono,
                    fontSize: 12,
                    letterSpacing: 0.48,
                    color: AppColors.ink3,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _joinedSince(DateTime? d) {
    if (d == null) return '';
    final now = DateTime.now();
    final days = now.difference(d).inDays;
    if (days <= 0) return '오늘 시작';
    if (days < 30) return '시작한 지 $days일';
    final months = (days / 30).floor();
    return '시작한 지 약 $months개월';
  }
}

/// 설정 리스트 — detail-profile.jsx v2.1 구조.
/// 관심 주제 편집(+선택 카테고리 detail) → 폰트 설정 → 다크 모드(Switch) →
/// 북마크 → 알림 → 앱 정보.
class _SettingsList extends ConsumerWidget {
  final UserProfile? profile;
  const _SettingsList({required this.profile});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ids = profile?.interests ?? const <String>[];
    final cats = ids
        .map((id) => kCategoryById[id])
        .whereType<Category>()
        .toList();
    final interestsDetail = cats.isEmpty
        ? (profile == null ? '로그인 후 설정할 수 있어요' : '아직 선택된 주제가 없어요')
        : '${cats.length}개 선택됨 · ${cats.map((c) => c.ko).join(', ')}';

    final fonts = ref.watch(fontSettingsProvider);
    final fontDetail =
        '${serifById(fonts.serifId).name.replaceAll(RegExp(r' KR$'), '')} · '
        '${sansById(fonts.sansId).name.replaceAll(RegExp(r' KR$'), '')} · '
        '${fonts.size.label}';

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.only(top: 16, bottom: 6),
            decoration: const BoxDecoration(
              border: Border(top: BorderSide(color: AppColors.line)),
            ),
            child: Text(
              '설정',
              style: TextStyle(
                fontFamily: AppFonts.sans,
                fontSize: 12,
                letterSpacing: 1.68,
                color: AppColors.ink3,
              ),
            ),
          ),
          _SettingRow(
            icon: AppIconName.sparkle,
            label: '관심 주제 편집',
            detail: interestsDetail,
            onTap: profile == null
                ? null
                : () => context.go('/onboarding?edit=true'),
            showDivider: true,
          ),
          _SettingRow(
            icon: AppIconName.newspaper,
            label: '폰트 설정',
            detail: fontDetail,
            onTap: () => context.push('/settings/fonts'),
            showDivider: true,
          ),
          _SettingRow(
            icon: AppIconName.sun,
            label: '다크 모드',
            trailing: Switch(value: false, onChanged: (_) {}),
            showDivider: true,
          ),
          const _SettingRow(
            icon: AppIconName.bookmark,
            label: '북마크',
            detail: '저장한 뉴스 보기',
            showDivider: true,
          ),
          const _SettingRow(
            icon: AppIconName.bell,
            label: '알림',
            detail: 'AM 07:30 · PM 18:00',
            showDivider: true,
          ),
          const _SettingRow(
            icon: AppIconName.info,
            label: '앱 정보',
            showDivider: false,
          ),
        ],
      ),
    );
  }
}

class _SettingRow extends StatelessWidget {
  final AppIconName icon;
  final String label;
  final String? detail;
  final Widget? trailing;
  final bool showDivider;
  final VoidCallback? onTap;

  const _SettingRow({
    required this.icon,
    required this.label,
    this.detail,
    this.trailing,
    required this.showDivider,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final row = Container(
      padding: const EdgeInsets.symmetric(vertical: 14),
      decoration: BoxDecoration(
        border: showDivider
            ? const Border(bottom: BorderSide(color: AppColors.lineSoft))
            : null,
      ),
      child: Row(
        children: [
          Container(
            width: 32, height: 32,
            decoration: BoxDecoration(
              color: AppColors.paper2,
              border: Border.all(color: AppColors.line),
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: Center(child: AppIcon(icon, size: 16, color: AppColors.ink2)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontFamily: AppFonts.serif,
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.ink,
                  ),
                ),
                if (detail != null) ...[
                  const SizedBox(height: 1),
                  Text(
                    detail!,
                    style: const TextStyle(
                      fontFamily: AppFonts.sans,
                      fontSize: 12,
                      color: AppColors.ink3,
                    ),
                  ),
                ],
              ],
            ),
          ),
          trailing ??
              const AppIcon(AppIconName.chevronRight, size: 16, color: AppColors.ink4),
        ],
      ),
    );

    if (onTap == null) return row;
    return InkWell(onTap: onTap, child: row);
  }
}

class _SignOutButton extends ConsumerWidget {
  const _SignOutButton();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
      child: TextButton(
        onPressed: () async {
          // signOut() 은 authStateProvider 를 흔들어 이 위젯을 즉시 dispose 하므로
          // notifier 인스턴스를 먼저 얻어놓고 두 작업을 병렬로 실행.
          final guest = ref.read(guestModeProvider.notifier);
          await Future.wait([
            guest.disable(),
            const AuthRepository().signOut(),
          ]);
        },
        child: Text(
          '로그아웃',
          style: TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: AppColors.ink,
          ),
        ),
      ),
    );
  }
}
