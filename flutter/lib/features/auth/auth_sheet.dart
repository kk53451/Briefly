import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import 'auth_repository.dart';
import 'guest_mode.dart';

/// 로그인 진입 시 표시되는 바텀시트.
/// 3개 소셜 버튼 + 게스트 링크 + 약관 안내.
class AuthSheet extends ConsumerStatefulWidget {
  const AuthSheet({super.key});

  @override
  ConsumerState<AuthSheet> createState() => _AuthSheetState();
}

class _AuthSheetState extends ConsumerState<AuthSheet> {
  final _auth = const AuthRepository();
  bool _busy = false;

  Future<void> _run(Future<void> Function() action) async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      await action();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('로그인 실패: $e')),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _continueAsGuest() async {
    await ref.read(guestModeProvider.notifier).enable();
    if (!mounted) return;
    context.go('/home');
  }

  @override
  Widget build(BuildContext context) {
    // scrim (뒤 반투명) + 하단 시트로 구성
    return Scaffold(
      backgroundColor: const Color(0x40000000), // 반투명 scrim
      body: Column(
        children: [
          // 탭하면 닫기
          Expanded(
            child: GestureDetector(
              onTap: () => Navigator.of(context).maybePop(),
              behavior: HitTestBehavior.opaque,
              child: const SizedBox.expand(),
            ),
          ),
          _Sheet(
            busy: _busy,
            onKakao: () => _run(_auth.signInWithKakao),
            onGoogle: () => _run(() => _auth.signInWithGoogle().then((_) {})),
            onGuest: _continueAsGuest,
          ),
        ],
      ),
    );
  }
}

class _Sheet extends StatelessWidget {
  final bool busy;
  final VoidCallback onKakao;
  final VoidCallback onGoogle;
  final VoidCallback onGuest;

  const _Sheet({
    required this.busy,
    required this.onKakao,
    required this.onGoogle,
    required this.onGuest,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.paper,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        border: Border(top: BorderSide(color: AppColors.ink, width: 3)),
        boxShadow: [
          BoxShadow(
            color: Color(0x33000000),
            blurRadius: 60,
            offset: Offset(0, -20),
          ),
        ],
      ),
      padding: const EdgeInsets.fromLTRB(28, 14, 28, 28),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // 드래그 핸들
            Container(
              width: 36,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppColors.ink3.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            // 헤더
            Column(
              children: [
                Text(
                  'SIGN IN',
                  style: TextStyle(
                    fontFamily: AppFonts.mono,
                    fontSize: 12,
                    letterSpacing: 2.4,
                    color: AppColors.ink3,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '계정으로 시작하기',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 6),
                Text(
                  '관심 카테고리가 기기 간 동기화됩니다.',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: AppFonts.serif,
                    fontSize: 14,
                    letterSpacing: -0.14,
                    color: AppColors.ink2,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 22),
            _SocialButton(
              brand: _SocialBrand.kakao,
              label: '카카오로 시작하기',
              onTap: busy ? null : onKakao,
            ),
            const SizedBox(height: 10),
            _SocialButton(
              brand: _SocialBrand.google,
              label: 'Google로 시작하기',
              onTap: busy ? null : onGoogle,
            ),
            const SizedBox(height: 10),
            _SocialButton(
              brand: _SocialBrand.apple,
              label: 'Apple로 시작하기',
              onTap: null,          // 출시 전 추가 예정
              disabled: true,
              note: 'SOON',
            ),
            const SizedBox(height: 18),
            TextButton(
              onPressed: busy ? null : onGuest,
              child: Text(
                '지금은 게스트로 둘러보기',
                style: TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 13,
                  color: AppColors.ink3,
                  decoration: TextDecoration.underline,
                  decorationColor: AppColors.ink3.withValues(alpha: 0.6),
                ),
              ),
            ),
            const SizedBox(height: 6),
            RichText(
              textAlign: TextAlign.center,
              text: const TextSpan(
                style: TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 12,
                  height: 1.6,
                  color: AppColors.ink3,
                ),
                children: [
                  TextSpan(text: '계속하면 '),
                  TextSpan(
                    text: '서비스 이용약관',
                    style: TextStyle(decoration: TextDecoration.underline),
                  ),
                  TextSpan(text: '과\n'),
                  TextSpan(
                    text: '개인정보 처리방침',
                    style: TextStyle(decoration: TextDecoration.underline),
                  ),
                  TextSpan(text: '에 동의하게 됩니다.'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

enum _SocialBrand { kakao, google, apple }

class _SocialButton extends StatelessWidget {
  final _SocialBrand brand;
  final String label;
  final VoidCallback? onTap;
  final bool disabled;
  final String? note;

  const _SocialButton({
    required this.brand,
    required this.label,
    required this.onTap,
    this.disabled = false,
    this.note,
  });

  @override
  Widget build(BuildContext context) {
    final (bg, fg, border) = switch (brand) {
      _SocialBrand.kakao  => (const Color(0xFFFEE500), const Color(0xFF1A1A1A), Colors.transparent),
      _SocialBrand.google => (Colors.white,             const Color(0xFF1F1F1F), const Color(0xFFDADCE0)),
      _SocialBrand.apple  => (Colors.black,             Colors.white,             Colors.transparent),
    };

    final effectiveBg = disabled ? bg.withValues(alpha: 0.4) : bg;
    final effectiveFg = disabled ? fg.withValues(alpha: 0.5) : fg;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        SizedBox(
          width: double.infinity,
          height: 52,
          child: Material(
            color: effectiveBg,
            shape: RoundedRectangleBorder(
              side: BorderSide(color: border),
              borderRadius: BorderRadius.circular(AppRadius.md),
            ),
            child: InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(AppRadius.md),
              // 디자인 스펙: 라벨은 버튼 전체 가로폭 기준 중앙, 아이콘은 좌측 절대 위치.
              child: Stack(
                children: [
                  Center(
                    child: Text(
                      label,
                      style: TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -0.1,
                        color: effectiveFg,
                      ),
                    ),
                  ),
                  Positioned(
                    left: 16,
                    top: 0,
                    bottom: 0,
                    child: Center(
                      child: _BrandIcon(brand: brand, color: effectiveFg),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        if (note != null)
          Positioned(
            right: 14,
            top: -8,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: AppColors.accent,
                borderRadius: BorderRadius.circular(AppRadius.sm),
              ),
              child: Text(
                note!,
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.72,
                  color: AppColors.paper,
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _BrandIcon extends StatelessWidget {
  final _SocialBrand brand;
  final Color color;

  const _BrandIcon({required this.brand, required this.color});

  @override
  Widget build(BuildContext context) {
    // 디자인 소스 icons.jsx 의 BrandIcon SVG 를 간단한 텍스트 글리프 대체.
    // 실제 제출 단계 전에 공식 브랜드 마크 SVG asset 으로 교체 예정.
    final glyph = switch (brand) {
      _SocialBrand.kakao  => 'K',
      _SocialBrand.google => 'G',
      _SocialBrand.apple  => '',
    };
    final child = brand == _SocialBrand.apple
        ? Icon(Icons.apple, size: 20, color: color)
        : Text(
            glyph,
            style: TextStyle(
              fontFamily: AppFonts.sans,
              fontSize: 16,
              fontWeight: FontWeight.w900,
              color: color,
            ),
          );
    return SizedBox(width: 20, height: 20, child: Center(child: child));
  }
}
