import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';
import 'features/settings/font_settings_controller.dart';

class BrieflyApp extends ConsumerWidget {
  const BrieflyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    final size = ref.watch(fontSettingsProvider).size;
    return MaterialApp.router(
      title: 'Briefly',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
      // 폰트 설정 글자 크기 (작게/보통/크게/아주 크게) 를 앱 전체 텍스트에 적용.
      // 시스템 textScaler 와 곱연산되도록 mq.textScaler.clamp 가 아닌 단순 곱셈 사용.
      builder: (context, child) {
        final mq = MediaQuery.of(context);
        // 시스템 textScale 위에 사용자 선택값을 곱한다 (보통=1.0 이면 시스템 그대로).
        final systemFactor = mq.textScaler.scale(1.0);
        return MediaQuery(
          data: mq.copyWith(
            textScaler: TextScaler.linear(systemFactor * size.mult),
          ),
          child: child ?? const SizedBox.shrink(),
        );
      },
    );
  }
}
