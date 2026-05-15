import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/news_card.dart';
import '../../shared/widgets/async_state_views.dart';
import '../../shared/widgets/cat_badge.dart';
import 'data/search_repository.dart';

/// 검색 화면 — pg_trgm 기반 부분일치 뉴스 검색.
/// 디자인: Briefly_design/screens/search.jsx 의 initial / results 두 상태.
class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _ctrl = TextEditingController();
  final _focus = FocusNode();

  @override
  void initState() {
    super.initState();
    // 진입 시 즉시 키보드 띄워 검색어 입력으로 바로 들어가게.
    WidgetsBinding.instance.addPostFrameCallback((_) => _focus.requestFocus());
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _focus.dispose();
    // searchQueryProvider 는 페이지를 벗어나도 살아있어, 화면 재진입 시
    // 이전 검색어로 인해 _Initial 대신 stale 결과가 잠깐 보인다. 닫을 때 리셋.
    ref.read(searchQueryProvider.notifier).state = '';
    super.dispose();
  }

  void _commit(String q) {
    final trimmed = q.trim();
    if (trimmed.length < 2) return;
    _ctrl.text = trimmed;
    _ctrl.selection = TextSelection.collapsed(offset: trimmed.length);
    ref.read(searchQueryProvider.notifier).state = trimmed;
    ref.read(recentSearchesProvider.notifier).add(trimmed);
  }

  @override
  Widget build(BuildContext context) {
    final query = ref.watch(searchQueryProvider);
    final showResults = query.trim().length >= 2;

    return Scaffold(
      backgroundColor: AppColors.paper,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            _SearchBar(
              controller: _ctrl,
              focus: _focus,
              onChanged: (v) =>
                  ref.read(searchQueryProvider.notifier).state = v,
              onSubmitted: _commit,
              onClear: () {
                _ctrl.clear();
                ref.read(searchQueryProvider.notifier).state = '';
                _focus.requestFocus();
              },
            ),
            Expanded(
              child: showResults
                  ? const _Results()
                  : _Initial(
                      onPickRecent: (q) {
                        _ctrl.text = q;
                        _ctrl.selection =
                            TextSelection.collapsed(offset: q.length);
                        ref.read(searchQueryProvider.notifier).state = q;
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SearchBar extends StatelessWidget {
  final TextEditingController controller;
  final FocusNode focus;
  final ValueChanged<String> onChanged;
  final ValueChanged<String> onSubmitted;
  final VoidCallback onClear;

  const _SearchBar({
    required this.controller,
    required this.focus,
    required this.onChanged,
    required this.onSubmitted,
    required this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(10, 10, 16, 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.ink, width: 2)),
      ),
      child: Row(
        children: [
          IconButton(
            onPressed: () => context.pop(),
            icon: const AppIcon(AppIconName.arrowLeft, size: 22),
            padding: const EdgeInsets.all(8),
            constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: Container(
              constraints: const BoxConstraints(minHeight: 48),
              padding: const EdgeInsets.symmetric(horizontal: 14),
              decoration: BoxDecoration(
                color: AppColors.paper2,
                border: Border.all(color: AppColors.line),
              ),
              child: Row(
                children: [
                  const AppIcon(
                    AppIconName.search, size: 18, color: AppColors.ink3),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: controller,
                      focusNode: focus,
                      textInputAction: TextInputAction.search,
                      onChanged: onChanged,
                      onSubmitted: onSubmitted,
                      style: const TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 16,
                        color: AppColors.ink,
                      ),
                      decoration: const InputDecoration(
                        hintText: '헤드라인, 키워드, 주제 검색',
                        hintStyle: TextStyle(
                          fontFamily: AppFonts.sans,
                          fontSize: 16,
                          color: AppColors.ink4,
                        ),
                        border: InputBorder.none,
                        isCollapsed: true,
                        contentPadding: EdgeInsets.zero,
                      ),
                    ),
                  ),
                  if (controller.text.isNotEmpty)
                    GestureDetector(
                      onTap: onClear,
                      child: const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                        child: AppIcon(
                          AppIconName.close, size: 16, color: AppColors.ink3),
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

class _Initial extends ConsumerWidget {
  final ValueChanged<String> onPickRecent;
  const _Initial({required this.onPickRecent});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recent = ref.watch(recentSearchesProvider);
    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 18, 24, 24),
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            const Text(
              '최근 검색',
              style: TextStyle(
                fontFamily: AppFonts.serif,
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.ink2,
              ),
            ),
            if (recent.isNotEmpty)
              GestureDetector(
                onTap: () =>
                    ref.read(recentSearchesProvider.notifier).clear(),
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 6, horizontal: 4),
                  child: Text(
                    '전체 삭제',
                    style: TextStyle(
                      fontFamily: AppFonts.sans,
                      fontSize: 13,
                      color: AppColors.ink3,
                    ),
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(height: 10),
        if (recent.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Text(
              '최근 검색어가 없어요. 위 입력창에 검색어를 입력해보세요.',
              style: TextStyle(
                fontFamily: AppFonts.sans,
                fontSize: 13,
                color: AppColors.ink4,
              ),
            ),
          )
        else
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final r in recent)
                _RecentChip(
                  label: r,
                  onTap: () => onPickRecent(r),
                  onRemove: () => ref
                      .read(recentSearchesProvider.notifier)
                      .remove(r),
                ),
            ],
          ),
      ],
    );
  }
}

class _RecentChip extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final VoidCallback onRemove;
  const _RecentChip({
    required this.label,
    required this.onTap,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 36),
        padding: const EdgeInsets.fromLTRB(14, 8, 8, 8),
        decoration: BoxDecoration(
          color: AppColors.paper2,
          border: Border.all(color: AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontFamily: AppFonts.sans,
                fontSize: 14,
                color: AppColors.ink2,
              ),
            ),
            const SizedBox(width: 6),
            GestureDetector(
              onTap: onRemove,
              behavior: HitTestBehavior.opaque,
              child: const Padding(
                padding: EdgeInsets.all(2),
                child: AppIcon(
                  AppIconName.close, size: 14, color: AppColors.ink4),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Results extends ConsumerWidget {
  const _Results();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(searchResultsProvider);
    return async.when(
      loading: () => const EditorialLoading(height: 200),
      error: (e, _) => CenteredScrollable(
        child: EditorialError(
          error: e,
          onRetry: () => ref.invalidate(searchResultsProvider),
        ),
      ),
      data: (results) {
        if (results.isEmpty) {
          return const CenteredScrollable(
            child: EditorialEmpty(
              message: '검색 결과가 없어요.\n다른 키워드로 시도해보세요.',
            ),
          );
        }
        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
          itemCount: results.length,
          itemBuilder: (_, i) => _ResultRow(
            card: results[i],
            showDivider: i < results.length - 1,
          ),
        );
      },
    );
  }
}

class _ResultRow extends StatelessWidget {
  final NewsCard card;
  final bool showDivider;
  const _ResultRow({required this.card, required this.showDivider});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.push('/news/${Uri.encodeComponent(card.newsId)}'),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          border: showDivider
              ? const Border(bottom: BorderSide(color: AppColors.lineSoft))
              : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CatBadge(cat: card.category),
                const SizedBox(width: 8),
                if (card.provider != null && card.provider!.isNotEmpty)
                  Text(
                    card.provider!,
                    style: const TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 12,
                      color: AppColors.ink3,
                    ),
                  ),
                if (card.timeLabel.isNotEmpty) ...[
                  const SizedBox(width: 6),
                  Text(
                    '· ${card.timeLabel}',
                    style: const TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 12,
                      color: AppColors.ink4,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 6),
            Text(
              card.title,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontFamily: AppFonts.serif,
                fontSize: 16,
                fontWeight: FontWeight.w700,
                height: 1.35,
                letterSpacing: -0.16,
                color: AppColors.ink,
              ),
            ),
            if (card.hilight != null && card.hilight!.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                card.hilight!,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 13,
                  height: 1.5,
                  color: AppColors.ink3,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
