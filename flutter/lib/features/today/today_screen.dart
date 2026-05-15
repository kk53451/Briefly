import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/headline_topic.dart';
import '../../shared/widgets/async_state_views.dart';
import '../../shared/widgets/cat_badge.dart';
import '../../shared/widgets/editorial_image.dart';
import 'data/headlines_repository.dart';
import 'today_loading_skeleton.dart';

/// today.jsx 의 두 가지 디자인.
/// - editorial: 정석 에디토리얼 카드 (variant A)
/// - magazine: 사진 풀블리드 + 그레이 오버레이 매거진 커버 (variant B)
enum _Variant { editorial, magazine }

/// 투데이 — AM/PM 토글 + variant 토글 + 카테고리를 가로지르는 헤드라인 카드 스와이프.
class TodayScreen extends ConsumerStatefulWidget {
  const TodayScreen({super.key});

  @override
  ConsumerState<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends ConsumerState<TodayScreen> {
  String _slot = _autoSlot();
  _Variant _variant = _Variant.editorial;
  int _idx = 0;
  late final PageController _pc = PageController();

  static String _autoSlot() {
    final hour = DateTime.now().toUtc().add(const Duration(hours: 9)).hour;
    return hour < 12 ? 'AM' : 'PM';
  }

  @override
  void dispose() {
    _pc.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final today = _todayKst();
    final args = (date: today, slot: _slot);
    final async = ref.watch(todayHeadlinesProvider(args));

    return Container(
      color: AppColors.paper,
      child: SafeArea(
        bottom: false,
        child: Column(
          children: [
            // 헤더(오늘의 브리핑 + AM/PM 토글)는 로딩/에러/데이터 모든 상태에서 유지.
            _Header(
              slot: _slot,
              variant: _variant,
              onSlotChanged: (s) {
                setState(() {
                  _slot = s;
                  _idx = 0;
                });
                if (_pc.hasClients) _pc.jumpToPage(0);
              },
              onVariantToggle: () => setState(() {
                _variant = _variant == _Variant.editorial
                    ? _Variant.magazine
                    : _Variant.editorial;
              }),
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async =>
                    ref.invalidate(todayHeadlinesProvider(args)),
                color: AppColors.ink,
                child: async.when(
                  // 헤더 유지 + body 영역에만 v2.1 design 의 skeleton 카드/풋터.
                  loading: () => const TodayLoadingSkeleton(),
                  error: (e, _) => CenteredScrollable(
                    child: EditorialError(
                      error: e,
                      onRetry: () =>
                          ref.invalidate(todayHeadlinesProvider(args)),
                    ),
                  ),
                  data: (topics) => topics.isEmpty
                      ? const CenteredScrollable(
                          child: EditorialEmpty(
                            message: '아직 오늘의 브리핑이 준비되지 않았어요.\n잠시 후 새로 고쳐 주세요.',
                          ),
                        )
                      : Column(
                          children: [
                            _Indicator(count: topics.length, active: _idx),
                            Expanded(
                              child: PageView.builder(
                                controller: _pc,
                                itemCount: topics.length,
                                onPageChanged: (i) => setState(() => _idx = i),
                                itemBuilder: (_, i) =>
                                    _variant == _Variant.editorial
                                        ? _HeadlineCard(topic: topics[i])
                                        : _MagazineCard(
                                            topic: topics[i],
                                            index: i,
                                          ),
                              ),
                            ),
                          ],
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 오늘 날짜 (KST). 디바이스 로컬 시간대(에뮬레이터 = GMT)와 무관하게 backend
/// 가 저장한 KST date 컬럼과 매칭되도록 UTC+9 기준으로 환산.
DateTime _todayKst() {
  final nowKst = DateTime.now().toUtc().add(const Duration(hours: 9));
  return DateTime(nowKst.year, nowKst.month, nowKst.day);
}

class _Header extends StatelessWidget {
  final String slot;
  final _Variant variant;
  final ValueChanged<String> onSlotChanged;
  final VoidCallback onVariantToggle;

  const _Header({
    required this.slot,
    required this.variant,
    required this.onSlotChanged,
    required this.onVariantToggle,
  });

  @override
  Widget build(BuildContext context) {
    // "오늘의 브리핑" 타이틀 + variant 토글 아이콘 + AM/PM.
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 14, 24, 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(
            '오늘의 브리핑',
            style: Theme.of(context).textTheme.displaySmall?.copyWith(
                  fontWeight: FontWeight.w900,
                ),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              _VariantToggle(variant: variant, onTap: onVariantToggle),
              const SizedBox(width: 8),
              _SlotToggle(slot: slot, onChanged: onSlotChanged),
            ],
          ),
        ],
      ),
    );
  }
}

/// editorial(A) ↔ magazine(B) 전환 — 현재 모드의 반대를 가리키는 아이콘을 보여줘
/// 탭하면 그 모드로 전환된다.
class _VariantToggle extends StatelessWidget {
  final _Variant variant;
  final VoidCallback onTap;
  const _VariantToggle({required this.variant, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final iconData = variant == _Variant.editorial
        ? Icons.image_outlined          // → 매거진(B) 로 전환
        : Icons.dashboard_outlined;     // → 카드(A) 로 전환
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 42, height: 42,
        decoration: BoxDecoration(
          color: AppColors.paper2,
          border: Border.all(color: AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Icon(iconData, size: 18, color: AppColors.ink2),
      ),
    );
  }
}

class _SlotToggle extends StatelessWidget {
  final String slot;
  final ValueChanged<String> onChanged;

  const _SlotToggle({required this.slot, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: AppColors.paper2,
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: AppColors.line),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final s in const ['AM', 'PM'])
            GestureDetector(
              onTap: () => onChanged(s),
              child: Container(
                constraints: const BoxConstraints(minHeight: 36, minWidth: 56),
                alignment: Alignment.center,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: slot == s ? AppColors.ink : Colors.transparent,
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                ),
                child: Text(
                  s == 'AM' ? '오전' : '오후',
                  style: TextStyle(
                    fontFamily: AppFonts.mono,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.52,
                    color: slot == s ? AppColors.paper : AppColors.ink3,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _Indicator extends StatelessWidget {
  final int count;
  final int active;
  const _Indicator({required this.count, required this.active});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 4, 24, 14),
      child: Row(
        children: [
          for (int i = 0; i < count; i++) ...[
            if (i > 0) const SizedBox(width: 4),
            Expanded(
              child: Container(
                height: 3,
                decoration: BoxDecoration(
                  color: i == active ? AppColors.ink : AppColors.line,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _HeadlineCard extends StatelessWidget {
  final HeadlineTopic topic;
  const _HeadlineCard({required this.topic});

  @override
  Widget build(BuildContext context) {
    final cat = topic.category;
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 16),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: AppColors.line),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0F281E14),
              blurRadius: 20,
              offset: Offset(0, 6),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 18, 22, 14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CatBadge(cat: cat, size: CatBadgeSize.md),
                    const SizedBox(height: 14),
                    Text(
                      topic.headline,
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            height: 1.2,
                            letterSpacing: -0.5,
                          ),
                    ),
                    if (topic.keywords.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: [
                          for (final k in topic.keywords)
                            // 칩은 텍스트 폭에 hug 되어야 하므로 alignment 를 두지 않는다.
                            // (alignment 가 있으면 Container 가 Wrap 의 maxWidth 까지 확장돼
                            //  칩이 한 줄 전체로 늘어남.) vertical padding 7 로 ~32px 자연 높이 확보.
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                              decoration: BoxDecoration(
                                color: cat.color.withValues(alpha: 0.05),
                                border: Border.all(color: cat.color.withValues(alpha: 0.2)),
                                borderRadius: BorderRadius.circular(AppRadius.sm),
                              ),
                              child: Text(
                                '#$k',
                                style: TextStyle(
                                  fontFamily: AppFonts.sans,
                                  fontSize: 13,
                                  height: 1.2,
                                  color: cat.color,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
              EditorialImage(
                url: topic.representativeImage,
                height: 170,
                label: '대표 사진',
                cat: cat,
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(22, 16, 22, 20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const AppIcon(AppIconName.sparkle, size: 13, color: AppColors.accent),
                        const SizedBox(width: 8),
                        Text(
                          'AI 요약',
                          style: TextStyle(
                            fontFamily: AppFonts.mono,
                            fontSize: 12,
                            letterSpacing: 1.68,
                            color: AppColors.accent,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      topic.summary,
                      style: const TextStyle(
                        fontFamily: AppFonts.serif,
                        fontSize: 16,
                        height: 1.75,
                        color: AppColors.ink,
                      ),
                    ),
                    const SizedBox(height: 18),
                    Container(
                      padding: const EdgeInsets.only(top: 14),
                      decoration: const BoxDecoration(
                        border: Border(top: BorderSide(color: AppColors.lineSoft)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '대표 기사',
                            style: TextStyle(
                              fontFamily: AppFonts.mono,
                              fontSize: 12,
                              letterSpacing: 1.68,
                              color: AppColors.ink3,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '"${topic.representativeTitle}"',
                            style: const TextStyle(
                              fontFamily: AppFonts.serif,
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              height: 1.5,
                              color: AppColors.ink2,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text.rich(
                            TextSpan(
                              style: const TextStyle(
                                fontFamily: AppFonts.sans,
                                fontSize: 13,
                                color: AppColors.ink3,
                              ),
                              children: [
                                TextSpan(text: '${topic.representativePress} · 관련 기사 '),
                                TextSpan(
                                  text: '${topic.clusterSize}건',
                                  style: const TextStyle(
                                    color: AppColors.accent,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// today.jsx variant B — 다큐멘터리 사진 풀블리드 + 그레이 오버레이 매거진 커버.
/// representativeImage 가 NetworkImage 로 들어가고, 그 위에 dark gradient + 콘텐츠.
/// 사진이 없는 토픽은 wireframe 의 placeholder gradient 로 fallback.
class _MagazineCard extends StatelessWidget {
  final HeadlineTopic topic;
  final int index;
  const _MagazineCard({required this.topic, required this.index});

  static const _bg = Color(0xFF1A1714);

  @override
  Widget build(BuildContext context) {
    final cat = topic.category;
    final image = topic.representativeImage;

    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: Stack(
          fit: StackFit.expand,
          children: [
            // 1) 사진 또는 fallback gradient.
            if (image != null && image.isNotEmpty)
              ColorFiltered(
                colorFilter: const ColorFilter.matrix(<double>[
                  0.40, 0.45, 0.10, 0, 0,
                  0.40, 0.45, 0.10, 0, 0,
                  0.40, 0.45, 0.10, 0, 0,
                  0,    0,    0,    1, 0,
                ]),
                child: Image.network(
                  image,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => const ColoredBox(color: _bg),
                ),
              )
            else
              const DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [Color(0xFF3A3530), Color(0xFF241F1B), _bg],
                  ),
                ),
              ),
            // 2) 잉크 오버레이 — 위에서 아래로 점점 진하게 깔아 텍스트 가독성 확보.
            const DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Color(0x331A1714),
                    Color(0x8C1A1714),
                    Color(0xD91A1714),
                  ],
                  stops: [0, 0.6, 1],
                ),
              ),
            ),
            // 3) 콘텐츠.
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 30, 28, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 8, height: 8,
                        decoration: BoxDecoration(
                          color: cat.color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        '${cat.ko} · 관련 기사 ${topic.clusterSize}건',
                        style: TextStyle(
                          fontFamily: AppFonts.mono,
                          fontSize: 12,
                          letterSpacing: 1.2,
                          color: AppColors.paper.withValues(alpha: 0.85),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  // 거대한 mono 인덱스 — 헤드라인이 그 위로 살짝 겹치도록 음수 마진.
                  Text(
                    '0${index + 1}',
                    style: TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 120,
                      fontWeight: FontWeight.w400,
                      height: 1,
                      letterSpacing: -6,
                      color: AppColors.paper.withValues(alpha: 0.22),
                    ),
                  ),
                  Transform.translate(
                    offset: const Offset(0, -38),
                    child: Text(
                      topic.headline,
                      style: const TextStyle(
                        fontFamily: AppFonts.serif,
                        fontSize: 36,
                        fontWeight: FontWeight.w900,
                        height: 1.08,
                        letterSpacing: -1.1,
                        color: AppColors.paper,
                        shadows: [
                          Shadow(
                            color: Color(0x59000000),
                            blurRadius: 12,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.only(left: 12),
                    decoration: const BoxDecoration(
                      border: Border(
                        left: BorderSide(color: AppColors.paper, width: 2),
                      ),
                    ),
                    child: Text(
                      topic.summary,
                      maxLines: 4,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontFamily: AppFonts.serif,
                        fontSize: 16,
                        height: 1.7,
                        color: AppColors.paper.withValues(alpha: 0.95),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      Expanded(
                        child: SizedBox(
                          height: 48,
                          child: ElevatedButton(
                            onPressed: () {},
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.paper,
                              foregroundColor: AppColors.ink,
                              elevation: 0,
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.zero,
                              ),
                            ),
                            child: const Text(
                              '자세히 보기',
                              style: TextStyle(
                                fontFamily: AppFonts.sans,
                                fontSize: 15,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Container(
                        width: 48, height: 48,
                        decoration: BoxDecoration(
                          color: AppColors.paper.withValues(alpha: 0.12),
                          border: Border.all(
                            color: AppColors.paper.withValues(alpha: 0.3),
                          ),
                        ),
                        child: const Icon(
                          Icons.bookmark_border_rounded,
                          size: 20,
                          color: AppColors.paper,
                        ),
                      ),
                    ],
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
