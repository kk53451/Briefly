import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 앱 세션이 없어도 "게스트로 둘러보기" 를 선택하면 메인 탭에 진입 가능.
/// Supabase RLS가 news_cards/frequencies/headlines 에 anon SELECT 를 허용하므로
/// 로그인 없이도 read 가 작동함. profile/bookmarks만 로그인 필요.
///
/// 저장 위치: SharedPreferences key 'guest_mode' = bool
class GuestModeNotifier extends StateNotifier<bool> {
  GuestModeNotifier() : super(false) {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      state = prefs.getBool(_key) ?? false;
    } catch (e) {
      if (kDebugMode) debugPrint('GuestMode load failed: $e');
    }
  }

  Future<void> enable() async {
    state = true;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_key, true);
  }

  Future<void> disable() async {
    state = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_key, false);
  }

  static const _key = 'guest_mode';
}

final guestModeProvider =
    StateNotifierProvider<GuestModeNotifier, bool>((_) => GuestModeNotifier());
