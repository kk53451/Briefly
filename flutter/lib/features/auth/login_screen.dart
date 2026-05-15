import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';

/// 로그인 초기 화면 (variant A: masthead 에디션)
/// - 거대한 "Briefly." 세리프 워드마크
/// - 라이브닷 + 회전 헤드라인 티커 (타이핑→홀드→삭제→다음)
/// - 세리프 이탤릭 태그라인
/// - 하단 CTA: 시작하기 → AuthSheet 열기
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen>
    with SingleTickerProviderStateMixin {
  static const _headlines = [
    '지방 경선결과 진행상황',
    '미국-이란 전쟁 상황',
    '동물원 늑대 탈출',
    '다주택자 과세율 변동',
    '유가 상승에 따른 물가',
    '서울시 민원 폭탄',
    'AI 규제 법안 국회 통과',
    '전국 기온 급강하 주의보',
    '코스피 3,200선 안착',
    '반도체 수출 호조',
  ];

  int _idx = 0;
  String _text = '';
  _TickerPhase _phase = _TickerPhase.typing;
  Timer? _timer;

  // 라이브닷 펄스 애니메이션
  late final AnimationController _pulse = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat(reverse: true);

  @override
  void initState() {
    super.initState();
    _tick();
  }

  void _tick() {
    _timer?.cancel();
    final current = _headlines[_idx % _headlines.length];
    switch (_phase) {
      case _TickerPhase.typing:
        if (_text.length < current.length) {
          _timer = Timer(const Duration(milliseconds: 70), () {
            setState(() => _text = current.substring(0, _text.length + 1));
            _tick();
          });
        } else {
          _phase = _TickerPhase.holding;
          _tick();
        }
      case _TickerPhase.holding:
        _timer = Timer(const Duration(milliseconds: 1400), () {
          setState(() => _phase = _TickerPhase.erasing);
          _tick();
        });
      case _TickerPhase.erasing:
        if (_text.isNotEmpty) {
          _timer = Timer(const Duration(milliseconds: 28), () {
            setState(() => _text = _text.substring(0, _text.length - 1));
            _tick();
          });
        } else {
          _phase = _TickerPhase.gap;
          _tick();
        }
      case _TickerPhase.gap:
        _timer = Timer(const Duration(milliseconds: 400), () {
          setState(() {
            _idx++;
            _phase = _TickerPhase.typing;
          });
          _tick();
        });
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulse.dispose();
    super.dispose();
  }

  void _start() {
    // 바텀시트로 Auth 열기
    context.pushNamed('auth-sheet');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.paper,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(28, 40, 28, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 히어로: 화면 중앙보다 약 40px 위에 배치 (design spec: marginTop -40)
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 40),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // 워드마크
                      RichText(
                        text: const TextSpan(
                          style: TextStyle(
                            fontFamily: AppFonts.serif,
                            fontWeight: FontWeight.w900,
                            fontSize: 82,
                            height: 0.92,
                            letterSpacing: -3.3,
                            color: AppColors.ink,
                          ),
                          children: [
                            TextSpan(text: 'Briefly'),
                            TextSpan(
                              text: '.',
                              style: TextStyle(color: AppColors.accent),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 44),
                      // 티커 라인 — 라이브닷 + 타이핑 텍스트 + caret
                      SizedBox(
                        height: 30,
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            AnimatedBuilder(
                              animation: _pulse,
                              builder: (_, _) {
                                final t = _pulse.value;
                                return Transform.scale(
                                  scale: 0.8 + (1 - t) * 0.2,
                                  child: Container(
                                    width: 7,
                                    height: 7,
                                    decoration: BoxDecoration(
                                      color: AppColors.accent.withValues(
                                        alpha: 0.35 + (1 - t) * 0.65,
                                      ),
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                );
                              },
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text.rich(
                                TextSpan(
                                  style: const TextStyle(
                                    fontFamily: AppFonts.serif,
                                    fontSize: 22,
                                    height: 1.3,
                                    letterSpacing: -0.22,
                                    color: AppColors.ink2,
                                  ),
                                  children: [
                                    TextSpan(text: _text),
                                    const WidgetSpan(
                                      alignment: PlaceholderAlignment.middle,
                                      child: _BlinkingCaret(),
                                    ),
                                  ],
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.clip,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),
                      // 태그라인
                      const Text(
                        '목소리로 편하게 듣는\n오늘의 헤드라인',
                        style: TextStyle(
                          fontFamily: AppFonts.serif,
                          fontWeight: FontWeight.w400,
                          fontSize: 26,
                          height: 1.3,
                          letterSpacing: -0.26,
                          color: AppColors.ink2,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              // CTA
              FilledButton(
                onPressed: _start,
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text(
                      '시작하기',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
                    ),
                    Icon(Icons.arrow_forward_rounded, size: 18),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

enum _TickerPhase { typing, holding, erasing, gap }

class _BlinkingCaret extends StatefulWidget {
  const _BlinkingCaret();

  @override
  State<_BlinkingCaret> createState() => _BlinkingCaretState();
}

class _BlinkingCaretState extends State<_BlinkingCaret>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 850),
  )..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _c,
      builder: (_, _) {
        final visible = _c.value < 0.5;
        return Opacity(
          opacity: visible ? 1 : 0,
          child: Container(
            width: 2,
            height: 20,
            margin: const EdgeInsets.only(left: 2, bottom: 2),
            color: AppColors.ink,
          ),
        );
      },
    );
  }
}
