import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/supabase.dart';
import '../../../shared/models/headline_topic.dart';

class HeadlinesRepository {
  const HeadlinesRepository();

  /// 지정 date+slot 의 모든 카테고리 headlines 를 fetch 하고,
  /// 각 카테고리의 top 1 토픽만 골라 합쳐 리턴한다 (최대 `max` 개).
  /// 프로토타입의 "오늘의 여섯 가지 이슈" UX 에 맞춰 카테고리 다양성을 보장.
  Future<List<HeadlineTopic>> topicsFor(
    DateTime date,
    String slot, {
    int max = 6,
  }) async {
    final d = _fmtDate(date);
    final rows = await supabase
        .from('headlines')
        .select('category, items')
        .eq('date', d)
        .eq('slot', slot);

    final topics = <HeadlineTopic>[];
    for (final row in (rows as List).cast<Map<String, dynamic>>()) {
      final category = (row['category'] as String?) ?? '';
      final items = row['items'];
      if (items is! List || items.isEmpty) continue;
      final first = items.first;
      if (first is! Map) continue;
      topics.add(HeadlineTopic.fromItem(
        Map<String, dynamic>.from(first),
        category,
      ));
    }
    // cluster_size 내림차순 정렬 후 max 개
    topics.sort((a, b) => b.clusterSize.compareTo(a.clusterSize));
    return topics.take(max).toList();
  }

  String _fmtDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
}

final headlinesRepositoryProvider =
    Provider<HeadlinesRepository>((_) => const HeadlinesRepository());

/// (date, slot) 파라미터 조합으로 오늘의 헤드라인 토픽 6개를 캐시.
final todayHeadlinesProvider = FutureProvider.family<List<HeadlineTopic>,
    ({DateTime date, String slot})>((ref, args) {
  return ref
      .read(headlinesRepositoryProvider)
      .topicsFor(args.date, args.slot, max: 6);
});
