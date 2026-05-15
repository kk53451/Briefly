import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Today 화면 body 영역의 로딩 스켈레톤.
/// Today 의 정규 헤더(`_Header` — "오늘의 브리핑" 타이틀 + AM/PM 토글)는
/// 그대로 유지되고, 그 아래 body 영역에 이 스켈레톤이 표시됩니다.
///
/// Briefly_design v2.1 (`Briefly_design/screens/states.jsx:LoadingState`) 의
/// 카드 + 풋터 부분만 발췌:
/// - 카드 내부: 카테고리/시간 바 + 제목 2줄 + 이미지 placeholder + body 3줄,
///   전부 shimmer sweep 애니메이션
/// - 풋터: "● 뉴스를 가져오고 있어요" pulse
///
/// design 의 `BrieflyMark + "● 가져오는 중"` 헤더 / `오늘의 브리핑` 큰 타이틀 /
/// 6분할 progress 는 정규 화면에 이미 헤더가 있으므로 중복 회피 차원에서 생략.
class TodayLoadingSkeleton extends StatefulWidget {
  const TodayLoadingSkeleton({super.key});

  @override
  State<TodayLoadingSkeleton> createState() => _TodayLoadingSkeletonState();
}

class _TodayLoadingSkeletonState extends State<TodayLoadingSkeleton>
    with TickerProviderStateMixin {
  late final AnimationController _shimmer;
  late final AnimationController _dotPulse;

  @override
  void initState() {
    super.initState();
    _shimmer = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat();
    _dotPulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _shimmer.dispose();
    _dotPulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // RefreshIndicator 가 위에서 감싸므로 AlwaysScrollable 로 두면 로딩 중에도
    // 사용자가 pull-to-refresh 시도 가능 (멈춰있을 때 탈출구).
    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // ── Skeleton 카드 ──
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 0),
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.card,
                border: Border.all(color: AppColors.line),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 상단: 카테고리/시간 메타
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _ShimmerBar(controller: _shimmer, width: 70, height: 10),
                      _ShimmerBar(controller: _shimmer, width: 40, height: 10),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // 제목 2줄
                  _ShimmerBar(
                    controller: _shimmer,
                    widthFactor: 0.85,
                    height: 20,
                  ),
                  const SizedBox(height: 8),
                  _ShimmerBar(
                    controller: _shimmer,
                    widthFactor: 0.65,
                    height: 20,
                  ),
                  const SizedBox(height: 18),
                  // 이미지 placeholder
                  _ShimmerBar(
                    controller: _shimmer,
                    widthFactor: 1.0,
                    height: 160,
                    diagonal: true,
                  ),
                  const SizedBox(height: 16),
                  // body 3줄
                  _ShimmerBar(controller: _shimmer, widthFactor: 1.0, height: 10),
                  const SizedBox(height: 6),
                  _ShimmerBar(controller: _shimmer, widthFactor: 1.0, height: 10),
                  const SizedBox(height: 6),
                  _ShimmerBar(controller: _shimmer, widthFactor: 0.8, height: 10),
                ],
              ),
            ),
          ),
          // ── 풋터: "● 뉴스를 가져오고 있어요" ──
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 22),
            child: Center(
              child: _PulsingLabel(
                pulse: _dotPulse,
                text: '뉴스를 가져오고 있어요',
                color: AppColors.accent,
                textStyle: const TextStyle(
                  fontFamily: AppFonts.serif,
                  fontSize: 16,
                  color: AppColors.ink2,
                ),
                spaceBetweenDotAndText: 10,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// "● 라벨" 형태로 dot 만 깜빡이는 위젯.
class _PulsingLabel extends StatelessWidget {
  final AnimationController pulse;
  final String text;
  final Color color;
  final TextStyle? textStyle;
  final double spaceBetweenDotAndText;

  const _PulsingLabel({
    required this.pulse,
    required this.text,
    required this.color,
    this.textStyle,
    this.spaceBetweenDotAndText = 6,
  });

  @override
  Widget build(BuildContext context) {
    final defaultStyle = TextStyle(
      fontFamily: AppFonts.mono,
      fontSize: 12,
      letterSpacing: 0.96,
      color: color,
    );
    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        AnimatedBuilder(
          animation: pulse,
          builder: (_, _) {
            // 0..1..0 (reverse repeat) → 0.2 ~ 1.0 alpha
            final t = pulse.value; // 0..1
            final alpha = 0.2 + (t * 0.8);
            return Text(
              '●',
              style: TextStyle(
                fontSize: (textStyle?.fontSize ?? defaultStyle.fontSize)! - 2,
                color: color.withValues(alpha: alpha),
                height: 1,
              ),
            );
          },
        ),
        SizedBox(width: spaceBetweenDotAndText),
        Text(text, style: textStyle ?? defaultStyle),
      ],
    );
  }
}

/// shimmer sweep 애니메이션이 적용된 가로 바.
/// `width` 가 주어지면 그 너비, 아니면 [widthFactor] 비율 (부모 너비 대비).
class _ShimmerBar extends StatelessWidget {
  final AnimationController controller;
  final double? width;
  final double widthFactor;
  final double height;
  final bool diagonal;

  const _ShimmerBar({
    required this.controller,
    this.width,
    this.widthFactor = 1.0,
    required this.height,
    this.diagonal = false,
  });

  @override
  Widget build(BuildContext context) {
    final bar = AnimatedBuilder(
      animation: controller,
      builder: (_, _) {
        // -1 → 2 사이로 슬라이드 (CSS keyframe translateX(-100%) → translateX(200%))
        final t = controller.value; // 0..1
        final shift = -1.0 + t * 3.0; // -1 .. +2
        return ClipRRect(
          borderRadius: BorderRadius.circular(2),
          child: Container(
            height: height,
            color: AppColors.paper2,
            child: FractionalTranslation(
              translation: Offset(shift, 0),
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: diagonal
                        ? Alignment.topLeft
                        : Alignment.centerLeft,
                    end: diagonal
                        ? Alignment.bottomRight
                        : Alignment.centerRight,
                    colors: diagonal
                        ? [
                            Colors.transparent,
                            const Color(0xFFF7F2E9).withValues(alpha: 0.5),
                            Colors.transparent,
                          ]
                        : [
                            Colors.transparent,
                            AppColors.accent.withValues(alpha: 0.08),
                            AppColors.accent.withValues(alpha: 0.22),
                            AppColors.accent.withValues(alpha: 0.08),
                            Colors.transparent,
                          ],
                    stops: diagonal
                        ? const [0.2, 0.5, 0.8]
                        : const [0.0, 0.4, 0.5, 0.6, 1.0],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
    if (width != null) {
      return SizedBox(width: width, child: bar);
    }
    return FractionallySizedBox(
      alignment: Alignment.centerLeft,
      widthFactor: widthFactor,
      child: bar,
    );
  }
}
