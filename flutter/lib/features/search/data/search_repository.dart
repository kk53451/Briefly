import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../../core/config/supabase.dart';
import '../../../shared/models/news_card.dart';

class SearchRepository {
  const SearchRepository();

  /// pg_trgm 기반 RPC `search_news_cards` 호출.
  /// 빈 쿼리/2자 미만은 RPC 가 빈 결과를 반환하지만, 네트워크 비용을 아끼기 위해
  /// 클라이언트에서 가드.
  Future<List<NewsCard>> search(String query, {int limit = 30}) async {
    final q = query.trim();
    if (q.length < 2) return const [];
    final rows = await supabase.rpc(
      'search_news_cards',
      params: {'q': q, 'lim': limit},
    );
    if (rows is! List) return const [];
    return rows
        .cast<Map<String, dynamic>>()
        .map(NewsCard.fromRow)
        .toList();
  }
}

final searchRepositoryProvider =
    Provider<SearchRepository>((_) => const SearchRepository());

/// 현재 입력된 검색어 — 뷰 단에서 setState 하지 않고 Riverpod 으로 들고 있어
/// 화면 회전/재생성 시에도 유지.
final searchQueryProvider = StateProvider<String>((_) => '');

/// 검색 결과 — searchQueryProvider 변경에 자동으로 재요청.
/// 200ms 디바운스: 타이핑 중 매 키스트로크마다 RPC 안 때리도록 한다.
/// dispose 후의 결과 무시는 ref.onDispose 로 cancel flag 를 세워 처리.
final searchResultsProvider =
    FutureProvider.autoDispose<List<NewsCard>>((ref) async {
  final q = ref.watch(searchQueryProvider);
  if (q.trim().length < 2) return const [];
  var cancelled = false;
  ref.onDispose(() => cancelled = true);
  await Future<void>.delayed(const Duration(milliseconds: 200));
  if (cancelled) return const [];
  return ref.read(searchRepositoryProvider).search(q);
});

// ─── 최근 검색어 (로컬 only) ────────────────────────────────────────────────
// supabase 에 저장하지 않고 SharedPreferences 에 디바이스별로 보관. 로그아웃 시
// 보존되는 게 의도 (게스트도 동일).

const _kRecentSearchesKey = 'search.recent';
const _kRecentSearchesMax = 8;

class RecentSearchesController extends StateNotifier<List<String>> {
  RecentSearchesController() : super(const []) {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    state = prefs.getStringList(_kRecentSearchesKey) ?? const [];
  }

  Future<void> add(String query) async {
    final q = query.trim();
    if (q.isEmpty) return;
    final next = [q, ...state.where((s) => s != q)].take(_kRecentSearchesMax).toList();
    state = next;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_kRecentSearchesKey, next);
  }

  Future<void> clear() async {
    state = const [];
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kRecentSearchesKey);
  }

  Future<void> remove(String query) async {
    state = state.where((s) => s != query).toList();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_kRecentSearchesKey, state);
  }
}

final recentSearchesProvider =
    StateNotifierProvider<RecentSearchesController, List<String>>(
  (_) => RecentSearchesController(),
);
