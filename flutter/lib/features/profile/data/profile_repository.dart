import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/config/supabase.dart';
import '../../../shared/models/user_profile.dart';
import '../../auth/auth_controller.dart';

class ProfileRepository {
  const ProfileRepository();

  /// 현재 로그인 사용자의 profile row. 게스트/비로그인 이면 null.
  Future<UserProfile?> fetchMe() async {
    final uid = supabase.auth.currentSession?.user.id;
    if (uid == null) return null;
    final row = await supabase
        .from('profiles')
        .select()
        .eq('id', uid)
        .maybeSingle();
    if (row == null) return null;
    return UserProfile.fromRow(row);
  }

  /// 온보딩/편집 저장. 선택한 카테고리 id 배열과 완료 플래그를 업데이트.
  Future<void> saveOnboarding({
    required List<String> interests,
    required bool markComplete,
  }) async {
    final uid = supabase.auth.currentSession?.user.id;
    if (uid == null) {
      throw StateError('로그인 필요');
    }
    await supabase.from('profiles').update({
      'interests': interests,
      if (markComplete) 'onboarding_completed': true,
    }).eq('id', uid);
  }
}

final profileRepositoryProvider =
    Provider<ProfileRepository>((_) => const ProfileRepository());

/// 로그인 세션 변화에 연동된 현재 사용자의 프로필.
/// 세션이 없으면 null → Profile 화면이 게스트 UI 로 분기.
final currentProfileProvider = FutureProvider<UserProfile?>((ref) async {
  // authStateProvider 를 watch 해서 로그인/로그아웃 시 자동 refetch.
  ref.watch(authStateProvider);
  return ref.read(profileRepositoryProvider).fetchMe();
});
