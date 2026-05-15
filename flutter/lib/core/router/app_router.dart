import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/auth_controller.dart';
import '../../features/auth/auth_sheet.dart';
import '../../features/auth/guest_mode.dart';
import '../../features/auth/login_screen.dart';
import '../../features/frequency/episodes_screen.dart';
import '../../features/frequency/podcast_screen.dart';
import '../../features/home/home_screen.dart';
import '../../features/news_detail/news_detail_screen.dart';
import '../../features/onboarding/onboarding_screen.dart';
import '../../features/profile/data/profile_repository.dart';
import '../../features/profile/profile_screen.dart';
import '../../features/search/search_screen.dart';
import '../../features/settings/font_settings_screen.dart';
import '../../features/shell/shell_scaffold.dart';
import '../../features/splash/splash_screen.dart';
import '../../features/today/today_screen.dart';
import '../config/supabase.dart';

final _rootKey = GlobalKey<NavigatorState>();
final _shellKey = GlobalKey<NavigatorState>();

final routerProvider = Provider<GoRouter>((ref) {
  final listenable = _AuthChangeNotifier(ref);
  ref.onDispose(listenable.dispose);

  return GoRouter(
    navigatorKey: _rootKey,
    initialLocation: '/',
    refreshListenable: listenable,
    redirect: (context, state) {
      final session = supabase.auth.currentSession;
      final isGuest = ref.read(guestModeProvider);
      final allowed = session != null || isGuest;

      final path = state.matchedLocation;
      final publicRoutes = {'/', '/login', '/auth-sheet'};

      // 1) 로그인도 아니고 게스트도 아님 → /login
      if (!allowed && !publicRoutes.contains(path) && path != '/onboarding') {
        return '/login';
      }

      // 2) 인증된 상태에서 /login 에 있는 경우 — profile 로딩이 끝나야
      //    목적지(/home 또는 /onboarding)를 **한 번에** 결정할 수 있음.
      //    로딩 중엔 그대로 /login 에 머물러 Home 화면 번쩍임을 방지.
      if (allowed && path == '/login') {
        if (session != null && !isGuest) {
          final p = ref.read(currentProfileProvider);
          if (p.isLoading) return null; // profile 준비될 때까지 대기
          final profile = p.valueOrNull;
          if (profile != null && !profile.onboardingCompleted) {
            return '/onboarding';
          }
        }
        return '/home';
      }

      // 3) 이미 다른 화면에 있는데 onboarding 미완료면 강제 /onboarding.
      if (session != null && !isGuest && path != '/onboarding') {
        final profile = ref.read(currentProfileProvider).valueOrNull;
        if (profile != null && !profile.onboardingCompleted) {
          return '/onboarding';
        }
      }
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, _) => const SplashScreen()),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(
        path: '/auth-sheet',
        name: 'auth-sheet',
        pageBuilder: (_, _) => CustomTransitionPage(
          opaque: false,
          barrierDismissible: true,
          barrierColor: const Color(0x40000000),
          transitionDuration: const Duration(milliseconds: 260),
          transitionsBuilder: (_, animation, _, child) => SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 1),
              end: Offset.zero,
            ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOut)),
            child: child,
          ),
          child: const AuthSheet(),
        ),
      ),
      GoRoute(
        path: '/onboarding',
        builder: (_, state) {
          final edit = state.uri.queryParameters['edit'] == 'true';
          return OnboardingScreen(editMode: edit);
        },
      ),
      GoRoute(
        path: '/news/:id',
        builder: (_, state) {
          // 일부 토픽의 representative_news_id 는 풀 Naver URL ("https://...")이라
          // push 단에서 URL-encode 한다. 화면에는 원본 ID 를 다시 디코드해서 전달.
          final raw = state.pathParameters['id'] ?? '';
          final decoded = Uri.decodeComponent(raw);
          return NewsDetailScreen(newsId: decoded);
        },
      ),
      GoRoute(path: '/episodes', builder: (_, _) => const EpisodesScreen()),
      GoRoute(path: '/search', builder: (_, _) => const SearchScreen()),
      GoRoute(
        path: '/settings/fonts',
        builder: (_, _) => const FontSettingsScreen(),
      ),
      StatefulShellRoute.indexedStack(
        parentNavigatorKey: _rootKey,
        builder: (_, _, nav) => ShellScaffold(
          currentIndex: nav.currentIndex,
          onTab: nav.goBranch,
          child: nav,
        ),
        branches: [
          StatefulShellBranch(
            navigatorKey: _shellKey,
            routes: [
              GoRoute(path: '/home', builder: (_, _) => const HomeScreen()),
            ],
          ),
          StatefulShellBranch(routes: [
            GoRoute(path: '/today', builder: (_, _) => const TodayScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: '/podcast', builder: (_, _) => const PodcastScreen()),
          ]),
          StatefulShellBranch(routes: [
            GoRoute(path: '/profile', builder: (_, _) => const ProfileScreen()),
          ]),
        ],
      ),
    ],
  );
});

class _AuthChangeNotifier extends ChangeNotifier {
  _AuthChangeNotifier(this._ref) {
    _authSub = _ref.listen<dynamic>(
      authStateProvider,
      (prev, next) => notifyListeners(),
    );
    _guestSub = _ref.listen<bool>(
      guestModeProvider,
      (prev, next) => notifyListeners(),
    );
    _profileSub = _ref.listen<dynamic>(
      currentProfileProvider,
      (prev, next) => notifyListeners(),
    );
  }

  final Ref _ref;
  late final ProviderSubscription<dynamic> _authSub;
  late final ProviderSubscription<bool> _guestSub;
  late final ProviderSubscription<dynamic> _profileSub;

  @override
  void dispose() {
    _authSub.close();
    _guestSub.close();
    _profileSub.close();
    super.dispose();
  }
}
