import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';

/// 콜드 스타트 splash — 0.8초 노출 후 라우팅 재평가.
/// (실제 라우팅은 GoRouter redirect 가 담당하므로 여기선 짧은 시각적 전환만)
class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Timer(const Duration(milliseconds: 800), () {
      if (!mounted) return;
      // router redirect 가 로그인/게스트/홈 중 적절한 곳으로 보냄.
      context.go('/login');
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.paper,
      body: Center(
        child: Text.rich(
          TextSpan(
            children: [
              TextSpan(text: 'Briefly'),
              TextSpan(text: '.', style: TextStyle(color: AppColors.accent)),
            ],
            style: TextStyle(
              fontFamily: AppFonts.serif,
              fontWeight: FontWeight.w900,
              fontSize: 72,
              height: 1,
              letterSpacing: -2.8,
              color: AppColors.ink,
            ),
          ),
        ),
      ),
    );
  }
}
