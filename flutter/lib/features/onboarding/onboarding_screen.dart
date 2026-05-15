import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants/categories.dart';
import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../profile/data/profile_repository.dart';

/// 온보딩 — 관심 카테고리 선택 (variant A: 2열 그리드).
/// - [editMode] true 면 Profile → "편집" 경로. 완료 시 `onboarding_completed`
///   플래그는 그대로 두고 `interests` 만 갱신, 완료 후 /profile 로 복귀.
class OnboardingScreen extends ConsumerStatefulWidget {
  final bool editMode;

  const OnboardingScreen({super.key, this.editMode = false});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final Set<String> _selected = {};
  bool _initialized = false;
  bool _saving = false;

  void _toggle(String id) {
    setState(() {
      if (_selected.contains(id)) {
        _selected.remove(id);
      } else {
        _selected.add(id);
      }
    });
  }

  Future<void> _finish() async {
    if (_selected.isEmpty || _saving) return;
    setState(() => _saving = true);

    final repo = ref.read(profileRepositoryProvider);
    try {
      await repo.saveOnboarding(
        interests: _selected.toList(),
        markComplete: true, // edit 모드에서도 true 로 유지 (이미 true 인 경우 noop)
      );
      // provider 를 invalidate 하고 새 fetch 가 끝날 때까지 await.
      // invalidate 만 하면 Router 가 이전 캐시값(onboardingCompleted=false) 으로
      // 오판해 /onboarding 으로 역-redirect 될 수 있음.
      ref.invalidate(currentProfileProvider);
      await ref.read(currentProfileProvider.future);
      if (!mounted) return;
      context.go(widget.editMode ? '/profile' : '/home');
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('저장 실패: $e')),
      );
      setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // 최초 진입 시 기존 interests 를 선택값으로 주입.
    if (!_initialized) {
      final profile = ref.watch(currentProfileProvider).valueOrNull;
      if (profile != null) {
        _selected.addAll(profile.interests);
        _initialized = true;
      } else if (!widget.editMode) {
        // 신규 온보딩: 기본 추천 4개 (하드뉴스 중심)
        _selected.addAll(const ['economy', 'politics', 'international', 'tech']);
        _initialized = true;
      }
    }

    final count = _selected.length;
    return Scaffold(
      backgroundColor: AppColors.paper,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 18, 24, 6),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_rounded, color: AppColors.ink3),
                    onPressed: widget.editMode ? () => context.pop() : null,
                  ),
                  const Spacer(),
                  Text(
                    widget.editMode ? '관심 주제 편집' : '2 / 2',
                    style: TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 12,
                      letterSpacing: 1.8,
                      color: AppColors.ink3,
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.editMode
                        ? '관심 주제를\n다시 골라주세요'
                        : '어떤 소식을\n전해드릴까요?',
                    style: Theme.of(context).textTheme.headlineLarge,
                  ),
                  const SizedBox(height: 10),
                  Text(
                    '선택한 주제 중심으로 오늘의 브리핑과 팟캐스트를 준비합니다.',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontSize: 14,
                          color: AppColors.ink2,
                        ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
                child: GridView.count(
                  crossAxisCount: 2,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 1.45,
                  children: kCategories.map((c) {
                    final sel = _selected.contains(c.id);
                    return _CategoryCard(
                      cat: c,
                      selected: sel,
                      onTap: () => _toggle(c.id),
                    );
                  }).toList(),
                ),
              ),
            ),
            Container(
              decoration: const BoxDecoration(
                color: AppColors.card,
                border: Border(top: BorderSide(color: AppColors.line)),
              ),
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 12),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Text(
                              '$count개',
                              style: TextStyle(
                                fontFamily: AppFonts.sans,
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: AppColors.accent,
                              ),
                            ),
                            Text(
                              ' 선택됨',
                              style: TextStyle(
                                fontFamily: AppFonts.sans,
                                fontSize: 14,
                                color: AppColors.ink2,
                              ),
                            ),
                          ],
                        ),
                        Text(
                          '최소 1개 이상',
                          style: TextStyle(
                            fontFamily: AppFonts.sans,
                            fontSize: 13,
                            color: AppColors.ink3,
                          ),
                        ),
                      ],
                    ),
                  ),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: count > 0 && !_saving ? _finish : null,
                      child: _saving
                          ? const SizedBox(
                              width: 18, height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2, color: AppColors.paper,
                              ),
                            )
                          : Text(widget.editMode ? '저장' : '시작하기'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CategoryCard extends StatelessWidget {
  final Category cat;
  final bool selected;
  final VoidCallback onTap;

  const _CategoryCard({required this.cat, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.md),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 140),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: selected ? cat.color : AppColors.card,
          border: Border.all(color: selected ? cat.color : AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.md),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: selected ? 0.08 : 0.03),
              blurRadius: selected ? 10 : 2,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          children: [
            AppIcon(
              cat.icon,
              size: 24,
              color: selected ? AppColors.paper : cat.color,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                cat.ko,
                style: TextStyle(
                  fontFamily: AppFonts.serif,
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.2,
                  color: selected ? AppColors.paper : AppColors.ink,
                ),
              ),
            ),
            if (selected)
              Container(
                width: 20,
                height: 20,
                decoration: const BoxDecoration(
                  color: AppColors.paper,
                  shape: BoxShape.circle,
                ),
                child: Icon(Icons.check_rounded, size: 13, color: cat.color),
              ),
          ],
        ),
      ),
    );
  }
}
