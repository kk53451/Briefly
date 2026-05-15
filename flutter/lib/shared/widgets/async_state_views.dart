import 'package:flutter/material.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';

/// `RefreshIndicator` 가 요구하는 스크롤 가능성을 유지하면서 [child] 를 뷰포트
/// 수직 중앙에 두고 싶을 때 사용. 보통 빈/에러 상태 fallback 을 감싸는 용도.
class CenteredScrollable extends StatelessWidget {
  final Widget child;
  const CenteredScrollable({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: ConstrainedBox(
          constraints: BoxConstraints(minHeight: constraints.maxHeight),
          child: Center(child: child),
        ),
      ),
    );
  }
}

/// 비동기 로드 상태 공통 뷰.
class EditorialLoading extends StatelessWidget {
  final double height;
  const EditorialLoading({super.key, this.height = 180});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: height,
      child: const Center(
        child: SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(
            strokeWidth: 2,
            color: AppColors.ink,
          ),
        ),
      ),
    );
  }
}

class EditorialEmpty extends StatelessWidget {
  final String message;

  /// 호환성을 위해 받지만 현재 구현은 [_StackedPaper] 일러스트로 고정.
  final IconData icon;

  const EditorialEmpty({
    super.key,
    required this.message,
    this.icon = Icons.article_outlined,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 40),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const _StackedPaper(badge: _PaperBadge.bookmark),
          const SizedBox(height: 24),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: AppFonts.serif,
              fontSize: 16,
              color: AppColors.ink3,
              height: 1.7,
            ),
          ),
        ],
      ),
    );
  }
}

class EditorialError extends StatelessWidget {
  final Object error;
  final VoidCallback? onRetry;
  const EditorialError({super.key, required this.error, this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 40),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const _StackedPaper(badge: _PaperBadge.exclaim),
          const SizedBox(height: 24),
          const Text(
            '오류가 발생했어요',
            style: TextStyle(
              fontFamily: AppFonts.serif,
              fontSize: 18,
              fontWeight: FontWeight.w800,
              letterSpacing: -0.36,
              color: AppColors.ink,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '$error',
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontFamily: AppFonts.mono,
              fontSize: 12,
              letterSpacing: 1.2,
              color: AppColors.ink4,
              height: 1.5,
            ),
          ),
          if (onRetry != null) ...[
            const SizedBox(height: 24),
            OutlinedButton(
              onPressed: onRetry,
              child: const Text('다시 시도'),
            ),
          ],
        ],
      ),
    );
  }
}

enum _PaperBadge { bookmark, exclaim }

/// states.jsx 의 종이 두 장 + 코너 배지 일러스트.
/// 한 장은 좌측으로 -4° 회전, 다른 한 장은 +3°. 우하단에 액센트 원형 배지.
class _StackedPaper extends StatelessWidget {
  final _PaperBadge badge;
  const _StackedPaper({required this.badge});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 120,
      height: 100,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // 뒷장 — 좌하단으로 살짝 어긋남, paper2 톤.
          Positioned(
            left: 14,
            top: 12,
            child: Transform.rotate(
              angle: -4 * 3.1415926 / 180,
              child: Container(
                width: 92,
                height: 72,
                decoration: BoxDecoration(
                  color: AppColors.paper2,
                  border: Border.all(color: AppColors.line),
                ),
              ),
            ),
          ),
          // 앞장 — 글줄 흉내내는 가는 라인 3줄.
          Positioned(
            left: 20,
            top: 6,
            child: Transform.rotate(
              angle: 3 * 3.1415926 / 180,
              child: Container(
                width: 92,
                height: 72,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  border: Border.all(color: AppColors.line),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    _PaperLine(widthFactor: 0.7),
                    SizedBox(height: 5),
                    _PaperLine(widthFactor: 0.9),
                    SizedBox(height: 5),
                    _PaperLine(widthFactor: 0.6),
                  ],
                ),
              ),
            ),
          ),
          // 우하단 액센트 배지.
          Positioned(
            right: 0,
            bottom: -8,
            child: Container(
              width: 36,
              height: 36,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                color: AppColors.accent,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: Color(0x26000000),
                    blurRadius: 12,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: badge == _PaperBadge.bookmark
                  ? const AppIcon(
                      AppIconName.bookmark,
                      size: 18,
                      color: AppColors.paper,
                    )
                  : const Text(
                      '!',
                      style: TextStyle(
                        fontFamily: AppFonts.serif,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        height: 1,
                        color: AppColors.paper,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class _PaperLine extends StatelessWidget {
  final double widthFactor;
  const _PaperLine({required this.widthFactor});

  @override
  Widget build(BuildContext context) {
    return FractionallySizedBox(
      alignment: Alignment.centerLeft,
      widthFactor: widthFactor,
      child: Container(height: 3, color: AppColors.line),
    );
  }
}
