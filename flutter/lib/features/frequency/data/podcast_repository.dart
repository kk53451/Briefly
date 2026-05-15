import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/supabase.dart';
import '../../../shared/models/episode.dart';

class PodcastRepository {
  const PodcastRepository();

  /// 최근 에피소드 N개를 (date desc, slot desc) 순으로 반환.
  /// slot 내 정렬: PM(오후) 가 AM(오전) 보다 먼저 나오도록 문자열 desc 정렬 사용.
  Future<List<Episode>> listRecent({int limit = 12}) async {
    final rows = await supabase
        .from('podcasts')
        .select()
        .order('date', ascending: false)
        .order('slot', ascending: false)
        .limit(limit);
    return (rows as List)
        .cast<Map<String, dynamic>>()
        .map(Episode.fromRow)
        .toList();
  }

  /// 특정 (date, slot) 에피소드. 없으면 null.
  Future<Episode?> byDateSlot(DateTime date, PodcastSlot slot) async {
    final d = _fmtDate(date);
    final row = await supabase
        .from('podcasts')
        .select()
        .eq('date', d)
        .eq('slot', slot.code)
        .maybeSingle();
    if (row == null) return null;
    return Episode.fromRow(row);
  }

  /// 오늘 기준 "재생 가능한" 가장 최근 에피소드 (audio_path 있는 것 중 최신).
  /// 없으면 목록 최상단 row (예정이거나 대본만 있는 경우).
  Future<Episode?> latestPlayable() async {
    final rows = await supabase
        .from('podcasts')
        .select()
        .not('audio_path', 'is', null)
        .order('date', ascending: false)
        .order('slot', ascending: false)
        .limit(1);
    final list = (rows as List).cast<Map<String, dynamic>>();
    if (list.isNotEmpty) return Episode.fromRow(list.first);

    // audio 없는 경우라도 가장 최근 row 를 대본용으로 반환
    final fallback = await supabase
        .from('podcasts')
        .select()
        .order('date', ascending: false)
        .order('slot', ascending: false)
        .limit(1);
    final fb = (fallback as List).cast<Map<String, dynamic>>();
    return fb.isEmpty ? null : Episode.fromRow(fb.first);
  }

  /// Storage public URL 만들어 반환. audio_path 없으면 null.
  String? publicUrl(String? audioPath) {
    if (audioPath == null || audioPath.isEmpty) return null;
    return supabase.storage.from('briefly-audio').getPublicUrl(audioPath);
  }

  String _fmtDate(DateTime d) {
    final y = d.year.toString().padLeft(4, '0');
    final m = d.month.toString().padLeft(2, '0');
    final da = d.day.toString().padLeft(2, '0');
    return '$y-$m-$da';
  }
}

final podcastRepositoryProvider =
    Provider<PodcastRepository>((_) => const PodcastRepository());

/// 현재 재생 대상 에피소드 — audio 있는 최신.
final currentEpisodeProvider = FutureProvider<Episode?>((ref) {
  return ref.read(podcastRepositoryProvider).latestPlayable();
});

/// 최근 에피소드 리스트 (플레이어 화면의 "최근 에피소드" + Episodes 화면).
final recentEpisodesProvider = FutureProvider<List<Episode>>((ref) {
  return ref.read(podcastRepositoryProvider).listRecent(limit: 14);
});
