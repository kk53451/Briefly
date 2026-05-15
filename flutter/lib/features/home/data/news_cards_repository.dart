import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/supabase.dart';
import '../../../shared/models/news_card.dart';

class NewsCardsRepository {
  const NewsCardsRepository();

  /// 특정 카테고리 + date 기준 rank 오름차순 리스트.
  /// slot 미지정이면 그 날의 가장 최근 slot (PM 우선) 자동 선택.
  Future<List<NewsCard>> byCategory({
    required String category,
    required DateTime date,
    String? slot,
    int limit = 20,
  }) async {
    final d = _fmtDate(date);
    var q = supabase
        .from('news_cards')
        .select()
        .eq('category', category)
        .eq('date', d);
    if (slot != null) q = q.eq('slot', slot);
    final rows = await q.order('rank', ascending: true).limit(limit);
    return (rows as List)
        .cast<Map<String, dynamic>>()
        .map(NewsCard.fromRow)
        .toList();
  }

  /// "종합" 탭용 — 각 카테고리의 rank=1 카드만 뽑아 리턴.
  Future<List<NewsCard>> topByCategory({required DateTime date}) async {
    final d = _fmtDate(date);
    final rows = await supabase
        .from('news_cards')
        .select()
        .eq('date', d)
        .eq('rank', 1)
        .order('cluster_size', ascending: false);
    return (rows as List)
        .cast<Map<String, dynamic>>()
        .map(NewsCard.fromRow)
        .toList();
  }

  /// news_id 단건 조회. 상세 화면용. 없으면 null.
  Future<NewsCard?> byId(String newsId) async {
    final row = await supabase
        .from('news_cards')
        .select()
        .eq('news_id', newsId)
        .maybeSingle();
    if (row == null) return null;
    return NewsCard.fromRow(row);
  }

  String _fmtDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

final newsCardsRepositoryProvider =
    Provider<NewsCardsRepository>((_) => const NewsCardsRepository());

/// Home 탭 상태: 선택된 카테고리 id ("all" | "economy" | …).
final homeActiveCategoryProvider = StateProvider<String>((_) => 'all');

/// 오늘(KST) 기준 카테고리별 뉴스 카드.
final homeNewsProvider = FutureProvider.family<List<NewsCard>, String>((
  ref,
  categoryId,
) async {
  final repo = ref.read(newsCardsRepositoryProvider);
  final today = _todayKst();
  if (categoryId == 'all') {
    return repo.topByCategory(date: today);
  }
  return repo.byCategory(category: categoryId, date: today);
});

/// 단건 news_card (상세 화면).
final newsCardByIdProvider =
    FutureProvider.family<NewsCard?, String>((ref, newsId) async {
  final repo = ref.read(newsCardsRepositoryProvider);
  return repo.byId(newsId);
});

/// 오늘 날짜 (KST 기준).
///
/// `DateTime.now()` 는 디바이스 로컬 시간대(에뮬레이터는 GMT 디폴트)를 쓰므로
/// 그대로 쓰면 UTC 자정 직전~KST 자정 사이 9시간 동안 전날로 잡혀 데이터가 안
/// 보이는 버그가 난다. backend 는 모든 date 컬럼을 KST 기준으로 저장하므로
/// 클라이언트도 KST 로 통일.
DateTime _todayKst() {
  final nowKst = DateTime.now().toUtc().add(const Duration(hours: 9));
  return DateTime(nowKst.year, nowKst.month, nowKst.day);
}
