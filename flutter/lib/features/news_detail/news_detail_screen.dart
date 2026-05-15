import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/news_card.dart';
import '../../shared/widgets/async_state_views.dart';
import '../../shared/widgets/cat_badge.dart';
import '../../shared/widgets/editorial_image.dart';
import '../home/data/news_cards_repository.dart';

/// 뉴스 상세 — Supabase news_cards 단건 조회 후 렌더.
class NewsDetailScreen extends ConsumerWidget {
  final String newsId;
  const NewsDetailScreen({super.key, required this.newsId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncCard = ref.watch(newsCardByIdProvider(newsId));

    return Scaffold(
      backgroundColor: AppColors.paper,
      body: SafeArea(
        child: asyncCard.when(
          loading: () => const EditorialLoading(height: 300),
          error: (e, _) => CenteredScrollable(
            child: EditorialError(
              error: e,
              onRetry: () => ref.invalidate(newsCardByIdProvider(newsId)),
            ),
          ),
          data: (card) {
            if (card == null) {
              return const CenteredScrollable(
                child: EditorialEmpty(message: '기사를 찾을 수 없습니다.'),
              );
            }
            return _DetailBody(card: card);
          },
        ),
      ),
    );
  }
}

class _DetailBody extends StatelessWidget {
  final NewsCard card;
  const _DetailBody({required this.card});

  @override
  Widget build(BuildContext context) {
    final cat = card.category;
    final hasOriginal = (card.providerLinkPage ?? '').isNotEmpty;

    return Column(
      children: [
        // Top bar
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 14, 24, 0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back_rounded),
                onPressed: () => context.pop(),
              ),
              Row(
                children: const [
                  AppIcon(AppIconName.bookmark, size: 20, color: AppColors.ink3),
                  SizedBox(width: 18),
                  AppIcon(AppIconName.share, size: 20, color: AppColors.ink3),
                  SizedBox(width: 18),
                  AppIcon(AppIconName.dots, size: 20, color: AppColors.ink3),
                ],
              ),
            ],
          ),
        ),
        // Body
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(24, 10, 24, 24),
            children: [
              CatBadge(cat: cat, size: CatBadgeSize.md),
              const SizedBox(height: 10),
              Text(
                card.title,
                style: const TextStyle(
                  fontFamily: AppFonts.serif,
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  height: 1.22,
                  letterSpacing: -0.5,
                  color: AppColors.ink,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                _metaLine(card),
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  letterSpacing: 0.48,
                  color: AppColors.ink3,
                ),
              ),
              const SizedBox(height: 16),
              EditorialImage(
                url: card.image,
                height: 220,
                cat: cat,
                label: '대표 사진',
              ),
              const SizedBox(height: 18),
              if ((card.hilight ?? '').isNotEmpty) ...[
                _AiSummaryBlock(summary: card.hilight!),
                const SizedBox(height: 22),
              ],
              if ((card.content ?? '').isNotEmpty)
                Text(
                  card.content!,
                  style: const TextStyle(
                    fontFamily: AppFonts.serif,
                    fontSize: 16,
                    height: 1.8,
                    color: AppColors.ink2,
                  ),
                ),
              const SizedBox(height: 22),
              _ClusterFootnote(clusterSize: card.clusterSize),
            ],
          ),
        ),
        // 원문 보기
        Container(
          decoration: const BoxDecoration(
            color: AppColors.card,
            border: Border(top: BorderSide(color: AppColors.line)),
          ),
          padding: const EdgeInsets.fromLTRB(24, 12, 24, 12),
          child: SafeArea(
            top: false,
            child: SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: hasOriginal
                    ? () => _openOriginal(context, card.providerLinkPage!)
                    : null,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Text('원문 보기'),
                    SizedBox(width: 8),
                    Icon(Icons.open_in_new_rounded, size: 14),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _AiSummaryBlock extends StatelessWidget {
  final String summary;
  const _AiSummaryBlock({required this.summary});

  @override
  Widget build(BuildContext context) {
    // IntrinsicHeight + stretch 로 좌측 accent line 이 우측 텍스트 높이에 맞춰
    // 자동으로 늘어나게 함. fixed height 면 요약이 길 때 line 끊겨 보임.
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(width: 3, color: AppColors.accent),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: const [
                    AppIcon(AppIconName.sparkle, size: 12, color: AppColors.accent),
                    SizedBox(width: 6),
                    Text(
                      '핵심 요약',
                      style: TextStyle(
                        fontFamily: AppFonts.mono,
                        fontSize: 12,
                        letterSpacing: 1.68,
                        color: AppColors.accent,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  summary,
                  style: const TextStyle(
                    fontFamily: AppFonts.serif,
                    fontSize: 16,
                    height: 1.7,
                    color: AppColors.ink,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ClusterFootnote extends StatelessWidget {
  final int clusterSize;
  const _ClusterFootnote({required this.clusterSize});

  @override
  Widget build(BuildContext context) {
    if (clusterSize <= 1) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: AppColors.paper2,
        borderRadius: BorderRadius.circular(AppRadius.sm),
      ),
      child: Text.rich(
        TextSpan(
          style: const TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: 12,
            height: 1.6,
            color: AppColors.ink3,
          ),
          children: [
            const TextSpan(text: '이 기사는 관련 보도 '),
            TextSpan(
              text: '$clusterSize건',
              style: const TextStyle(
                color: AppColors.ink,
                fontWeight: FontWeight.w700,
              ),
            ),
            const TextSpan(text: '의 대표 기사입니다.'),
          ],
        ),
      ),
    );
  }
}

String _metaLine(NewsCard n) {
  final parts = <String>[];
  if (n.provider != null && n.provider!.isNotEmpty) parts.add(n.provider!);
  final p = n.publishedAt;
  if (p != null) {
    final local = p.toLocal();
    parts.add(
      '${local.year}. ${local.month}. ${local.day}. · '
      '${local.hour.toString().padLeft(2, '0')}:${local.minute.toString().padLeft(2, '0')}',
    );
  }
  if (n.byline != null && n.byline!.isNotEmpty) parts.add(n.byline!);
  return parts.join(' · ');
}

Future<void> _openOriginal(BuildContext context, String url) async {
  final uri = Uri.tryParse(url);
  if (uri == null) return;
  final ok = await launchUrl(uri, mode: LaunchMode.externalApplication);
  if (!ok && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('원문 페이지를 열 수 없습니다.')),
    );
  }
}
