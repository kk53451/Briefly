import 'package:flutter/material.dart';

/// Briefly "warm editorial" tokens (briefly.css 포팅).
/// briefly.css의 :root 변수와 1:1 대응.
class AppColors {
  // Paper & ink
  static const paper   = Color(0xFFF7F2E9); // 바탕지 (크림)
  static const paper2  = Color(0xFFEFE8DA); // 보조 surface
  static const card    = Color(0xFFFCFAF4); // 카드 배경
  static const ink     = Color(0xFF1A1714); // 먹
  static const ink2    = Color(0xFF4A423B); // body 보조
  static const ink3    = Color(0xFF857A6D); // 메타 / 날짜
  static const ink4    = Color(0xFFB8AD9D); // 3차
  static const line    = Color(0xFFDCD3C1); // divider
  static const lineSoft = Color(0xFFE8E0CD);

  // Accent — rust
  static const accent     = Color(0xFFA03A28);
  static const accentSoft = Color(0xFFEADBC9);
  static const accentInk  = Color(0xFF6B2416);
}

class AppFonts {
  static const serif = 'NotoSerifKR';
  static const sans  = 'Pretendard';
  static const mono  = 'JetBrainsMono';
}

class AppRadius {
  static const sm = 2.0;
  static const md = 4.0;
  static const lg = 8.0;
  static const xl = 12.0;
  static const pill = 999.0;
}

class AppTheme {
  static ThemeData get light {
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: AppColors.ink,
      onPrimary: AppColors.paper,
      secondary: AppColors.accent,
      onSecondary: AppColors.paper,
      error: AppColors.accent,
      onError: AppColors.paper,
      surface: AppColors.paper,
      onSurface: AppColors.ink,
      surfaceContainerHighest: AppColors.card,
      outline: AppColors.line,
      outlineVariant: AppColors.lineSoft,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppColors.paper,
      fontFamily: AppFonts.sans,
      textTheme: _textTheme(AppColors.ink, AppColors.ink2),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.paper,
        foregroundColor: AppColors.ink,
        surfaceTintColor: Colors.transparent,
        scrolledUnderElevation: 0,
        centerTitle: false,
        elevation: 0,
      ),
      dividerTheme: const DividerThemeData(color: AppColors.line, thickness: 1, space: 1),
      iconTheme: const IconThemeData(color: AppColors.ink, size: 20),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.ink,
          foregroundColor: AppColors.paper,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(AppRadius.sm)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          textStyle: const TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: 15,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.1,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.ink,
          side: const BorderSide(color: AppColors.ink, width: 1),
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(AppRadius.sm)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          textStyle: const TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  static ThemeData get dark {
    // 지금은 라이트와 동일 (다크모드 variants는 이후 단계).
    // 요구사항이 들어오면 paper/ink를 반전시킨 팔레트로 재작성.
    return light;
  }

  static TextTheme _textTheme(Color ink, Color ink2) {
    // 프로토타입에서 자주 쓰이는 세리프/산스 조합을 디자인 토큰으로 고정.
    return TextTheme(
      displayLarge: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w900,
        fontSize: 82, height: 0.92, letterSpacing: -3.3, color: ink,
      ),
      displayMedium: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w900,
        fontSize: 44, height: 1.02, letterSpacing: -1.5, color: ink,
      ),
      displaySmall: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w900,
        fontSize: 32, height: 1.1, letterSpacing: -1.0, color: ink,
      ),
      headlineLarge: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w700,
        fontSize: 30, height: 1.15, letterSpacing: -0.6, color: ink,
      ),
      headlineMedium: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w700,
        fontSize: 26, height: 1.2, letterSpacing: -0.5, color: ink,
      ),
      headlineSmall: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w700,
        fontSize: 22, height: 1.2, letterSpacing: -0.45, color: ink,
      ),
      titleLarge: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w700,
        fontSize: 20, height: 1.25, letterSpacing: -0.35, color: ink,
      ),
      titleMedium: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w700,
        fontSize: 18, height: 1.3, letterSpacing: -0.3, color: ink,
      ),
      titleSmall: TextStyle(
        fontFamily: AppFonts.sans, fontWeight: FontWeight.w600,
        fontSize: 14, letterSpacing: -0.1, color: ink,
      ),
      bodyLarge: TextStyle(
        fontFamily: AppFonts.serif, fontWeight: FontWeight.w400,
        fontSize: 16, height: 1.7, color: ink,
      ),
      bodyMedium: TextStyle(
        fontFamily: AppFonts.sans, fontWeight: FontWeight.w400,
        fontSize: 14, height: 1.55, color: ink2,
      ),
      bodySmall: TextStyle(
        fontFamily: AppFonts.sans, fontWeight: FontWeight.w400,
        fontSize: 12, height: 1.5, color: AppColors.ink3,
      ),
      labelLarge: TextStyle(
        fontFamily: AppFonts.sans, fontWeight: FontWeight.w600,
        fontSize: 13, letterSpacing: -0.1, color: ink,
      ),
      // "mono" label 스타일 — JetBrainsMono + letter-spacing
      labelMedium: TextStyle(
        fontFamily: AppFonts.mono, fontWeight: FontWeight.w500,
        fontSize: 13, letterSpacing: 1.3, color: AppColors.ink3,
      ),
      labelSmall: TextStyle(
        fontFamily: AppFonts.mono, fontWeight: FontWeight.w500,
        fontSize: 12, letterSpacing: 1.6, color: AppColors.ink3,
      ),
    );
  }
}
