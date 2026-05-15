import '../../core/constants/categories.dart';

/// `public.news_cards` 한 행 — Home/Today 피드용 카드.
class NewsCard {
  final String newsId;
  final String categoryId;
  final DateTime date;
  final String slot;       // 'AM' | 'PM'
  final int rank;
  final int clusterSize;
  final String title;
  final String? image;
  final String? providerLinkPage;
  final String? provider;
  final String? byline;
  final DateTime? publishedAt;
  final String? hilight;
  final String? content;
  final DateTime collectedAt;

  const NewsCard({
    required this.newsId,
    required this.categoryId,
    required this.date,
    required this.slot,
    required this.rank,
    required this.clusterSize,
    required this.title,
    required this.image,
    required this.providerLinkPage,
    required this.provider,
    required this.byline,
    required this.publishedAt,
    required this.hilight,
    required this.content,
    required this.collectedAt,
  });

  Category get category =>
      kCategoryById[categoryId] ?? kCategories.first;

  factory NewsCard.fromRow(Map<String, dynamic> row) {
    DateTime? tsOrNull(dynamic v) =>
        (v is String && v.isNotEmpty) ? DateTime.tryParse(v) : null;
    return NewsCard(
      newsId: row['news_id'] as String,
      categoryId: (row['category'] as String?) ?? '',
      date: DateTime.parse(row['date'] as String),
      slot: (row['slot'] as String?) ?? 'AM',
      rank: (row['rank'] as num?)?.toInt() ?? 0,
      clusterSize: (row['cluster_size'] as num?)?.toInt() ?? 0,
      title: (row['title'] as String?) ?? '',
      // 본문 첫 사진(og:image, 원본 해상도) 우선, 없으면 목록 페이지 작은 썸네일.
      image: (row['hero_image'] as String?)?.isNotEmpty == true
          ? row['hero_image'] as String
          : ((row['images'] as String?)?.isNotEmpty == true
              ? row['images'] as String
              : null),
      providerLinkPage: row['provider_link_page'] as String?,
      provider: row['provider'] as String?,
      byline: row['byline'] as String?,
      publishedAt: tsOrNull(row['published_at']),
      hilight: row['hilight'] as String?,
      content: row['content'] as String?,
      collectedAt:
          tsOrNull(row['collected_at']) ?? DateTime.now(),
    );
  }

  /// 표시용 "HH:mm" — publishedAt 없으면 빈 문자열.
  String get timeLabel {
    final p = publishedAt;
    if (p == null) return '';
    final local = p.toLocal();
    final h = local.hour.toString().padLeft(2, '0');
    final m = local.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }
}
