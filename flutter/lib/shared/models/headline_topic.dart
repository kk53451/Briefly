import '../../core/constants/categories.dart';

/// `headlines.items` 의 단일 토픽 엔트리 (JSONB 내부 객체).
/// 파이프라인 save_headlines 의 item dict 와 1:1 매칭.
class HeadlineTopic {
  final int topicId;
  final String categoryId;      // 행의 category (예: 'economy')
  final String headline;
  final String summary;
  final int clusterSize;
  final String representativeNewsId;
  final String representativeTitle;
  final String? representativeImage;
  final String representativePress;
  final List<String> keywords;

  const HeadlineTopic({
    required this.topicId,
    required this.categoryId,
    required this.headline,
    required this.summary,
    required this.clusterSize,
    required this.representativeNewsId,
    required this.representativeTitle,
    required this.representativeImage,
    required this.representativePress,
    required this.keywords,
  });

  Category get category =>
      kCategoryById[categoryId] ?? kCategories.first;

  factory HeadlineTopic.fromItem(
      Map<String, dynamic> item, String categoryId) {
    final kwRaw = item['keywords'];
    final keywords = kwRaw is List
        ? kwRaw.whereType<String>().toList()
        : const <String>[];
    // 본문 첫 사진(원본 해상도) 우선, 없으면 작은 썸네일 폴백.
    final hero = item['representative_hero_image'] as String?;
    final thumb = item['representative_image'] as String?;
    final image = (hero != null && hero.isNotEmpty)
        ? hero
        : ((thumb != null && thumb.isNotEmpty) ? thumb : null);
    return HeadlineTopic(
      topicId: (item['topic_id'] as num?)?.toInt() ?? 0,
      categoryId: categoryId,
      headline: (item['headline'] as String?) ?? '',
      summary: (item['summary'] as String?) ?? '',
      clusterSize: (item['cluster_size'] as num?)?.toInt() ?? 0,
      representativeNewsId:
          (item['representative_news_id'] as String?) ?? '',
      representativeTitle: (item['representative_title'] as String?) ?? '',
      representativeImage: image,
      representativePress: (item['representative_press'] as String?) ?? '',
      keywords: keywords,
    );
  }
}
