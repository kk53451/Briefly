import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants/categories.dart';
import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/news_card.dart';
import '../../shared/widgets/async_state_views.dart';
import '../../shared/widgets/cat_badge.dart';
import '../../shared/widgets/editorial_image.dart';
import 'data/news_cards_repository.dart';

/// 홈 탭 (variant A) — 마스트헤드 + 카테고리 탭 + 리드 기사 + 랭킹 리스트.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activeId = ref.watch(homeActiveCategoryProvider);
    final asyncNews = ref.watch(homeNewsProvider(activeId));

    return Container(
      color: AppColors.paper,
      child: SafeArea(
        bottom: false,
        child: Column(
          children: [
            const _Masthead(),
            _CategoryTabs(
              activeId: activeId,
              onSelected: (id) =>
                  ref.read(homeActiveCategoryProvider.notifier).state = id,
            ),
            const _SortBar(),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async =>
                    ref.invalidate(homeNewsProvider(activeId)),
                color: AppColors.ink,
                child: asyncNews.when(
                  loading: () => const EditorialLoading(height: 300),
                  error: (e, _) => CenteredScrollable(
                    child: EditorialError(
                      error: e,
                      onRetry: () =>
                          ref.invalidate(homeNewsProvider(activeId)),
                    ),
                  ),
                  data: (news) => news.isEmpty
                      ? const CenteredScrollable(
                          child: EditorialEmpty(message: '표시할 뉴스가 없어요.'),
                        )
                      : _NewsList(news: news, mixedCategories: activeId == 'all'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 홈 상단 검색 바 — 네모 사각형 외곽선 + 검색 아이콘 + placeholder.
/// 탭 시 `/search` 로 이동.
class _Masthead extends StatelessWidget {
  const _Masthead();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 14, 24, 10),
      child: SizedBox(
        height: 44,
        child: Material(
          color: AppColors.paper,
          shape: const RoundedRectangleBorder(
            side: BorderSide(color: AppColors.line),
            borderRadius: BorderRadius.zero,
          ),
          child: InkWell(
            onTap: () => context.push('/search'),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: Row(
                children: const [
                  AppIcon(AppIconName.search, size: 18, color: AppColors.ink3),
                  SizedBox(width: 10),
                  Text(
                    '검색',
                    style: TextStyle(
                      fontFamily: AppFonts.sans,
                      fontSize: 14,
                      color: AppColors.ink4,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _CategoryTabs extends StatelessWidget {
  final String activeId;
  final ValueChanged<String> onSelected;

  const _CategoryTabs({required this.activeId, required this.onSelected});

  @override
  Widget build(BuildContext context) {
    final tabs = <({String id, String label, Color color})>[
      (id: 'all', label: '종합', color: AppColors.ink),
      (id: 'my', label: 'MY', color: AppColors.ink),
      for (final c in kCategories) (id: c.id, label: c.ko, color: c.color),
    ];
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.line)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Row(
          children: [
            for (final t in tabs)
              GestureDetector(
                onTap: () => onSelected(t.id),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: t.id == activeId ? t.color : Colors.transparent,
                        width: 2,
                      ),
                    ),
                  ),
                  child: Text(
                    t.label,
                    style: TextStyle(
                      fontFamily: AppFonts.serif,
                      fontSize: 16,
                      fontWeight: t.id == activeId ? FontWeight.w700 : FontWeight.w500,
                      letterSpacing: -0.16,
                      color: t.id == activeId ? AppColors.ink : AppColors.ink3,
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

class _SortBar extends StatelessWidget {
  const _SortBar();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 12, 24, 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const AppIcon(AppIconName.sort, size: 14, color: AppColors.ink2),
              const SizedBox(width: 6),
              Text(
                '트렌드순',
                style: TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.ink2,
                ),
              ),
              const SizedBox(width: 2),
              const AppIcon(AppIconName.chevronDown, size: 14, color: AppColors.ink2),
            ],
          ),
          Text(
            '방금 업데이트됨',
            style: TextStyle(
              fontFamily: AppFonts.mono,
              fontSize: 12,
              letterSpacing: 0.48,
              color: AppColors.ink3,
            ),
          ),
        ],
      ),
    );
  }
}

class _NewsList extends StatelessWidget {
  final List<NewsCard> news;
  final bool mixedCategories;
  const _NewsList({required this.news, required this.mixedCategories});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
      itemCount: news.length,
      itemBuilder: (_, i) {
        final n = news[i];
        if (i == 0) return _LeadStory(card: n);
        return _NewsRow(
          card: n,
          showDivider: i < news.length - 1,
        );
      },
    );
  }
}

class _LeadStory extends StatelessWidget {
  final NewsCard card;
  const _LeadStory({required this.card});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => context.push('/news/${Uri.encodeComponent(card.newsId)}'),
      child: Container(
        padding: const EdgeInsets.only(bottom: 18),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: AppColors.line)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            EditorialImage(
              url: card.image,
              height: 180,
              label: '리드 사진',
              cat: card.category,
            ),
            const SizedBox(height: 12),
            CatBadge(cat: card.category),
            const SizedBox(height: 8),
            Text(
              card.title,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                    letterSpacing: -0.4,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              _metaLine(card),
              style: const TextStyle(
                fontFamily: AppFonts.sans,
                fontSize: 12,
                color: AppColors.ink3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NewsRow extends StatelessWidget {
  final NewsCard card;
  final bool showDivider;
  const _NewsRow({required this.card, required this.showDivider});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.push('/news/${Uri.encodeComponent(card.newsId)}'),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          border: showDivider
              ? const Border(bottom: BorderSide(color: AppColors.lineSoft))
              : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        '#${card.rank}',
                        style: const TextStyle(
                          fontFamily: AppFonts.mono,
                          fontSize: 12,
                          letterSpacing: 0.96,
                          color: AppColors.ink3,
                        ),
                      ),
                      const SizedBox(width: 8),
                      CatBadge(cat: card.category),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    card.title,
                    style: const TextStyle(
                      fontFamily: AppFonts.serif,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      height: 1.35,
                      letterSpacing: -0.16,
                      color: AppColors.ink,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _metaLine(card),
                    style: const TextStyle(
                      fontFamily: AppFonts.sans,
                      fontSize: 12,
                      color: AppColors.ink3,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 14),
            EditorialImage(
              url: card.image,
              width: 84,
              height: 84,
              label: '${card.rank}',
              cat: card.category,
            ),
          ],
        ),
      ),
    );
  }
}

String _metaLine(NewsCard n) {
  final parts = <String>[];
  if (n.provider != null && n.provider!.isNotEmpty) parts.add(n.provider!);
  parts.add('관련 ${n.clusterSize}건');
  if (n.timeLabel.isNotEmpty) parts.add(n.timeLabel);
  return parts.join(' · ');
}
