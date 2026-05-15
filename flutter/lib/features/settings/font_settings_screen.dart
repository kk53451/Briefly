import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import 'font_settings_controller.dart';

/// 폰트 설정 화면 — 디자인 패키지 font-settings.jsx 포팅.
/// 좌측 back / 가운데 타이틀 / 우측 "변경됨" 표시 + 미리보기 + 드롭다운 2개 + 4-grid size + 하단 reset/apply.
class FontSettingsScreen extends ConsumerStatefulWidget {
  const FontSettingsScreen({super.key});

  @override
  ConsumerState<FontSettingsScreen> createState() => _FontSettingsScreenState();
}

class _FontSettingsScreenState extends ConsumerState<FontSettingsScreen> {
  late FontSettings _draft;
  String? _openDropdown; // 'serif' | 'sans' | null
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      _draft = ref.read(fontSettingsProvider);
      _initialized = true;
    }
  }

  bool _isDirty(FontSettings applied) =>
      _draft.serifId != applied.serifId ||
      _draft.sansId != applied.sansId ||
      _draft.size != applied.size;

  @override
  Widget build(BuildContext context) {
    final applied = ref.watch(fontSettingsProvider);
    final dirty = _isDirty(applied);
    final draftSerif = serifById(_draft.serifId);
    final draftSans = sansById(_draft.sansId);

    // 이 화면은 사용자가 "글자 크기" 효과를 미리보기에서 정확히 비교해야 하므로
    // 앱 전역 textScaler (적용된 size.mult) 의 영향을 받지 않도록 noScaling 으로 고정.
    // 미리보기/옵션 샘플은 _draft.size.mult 를 fontSize 에 직접 곱해서 보여준다.
    return MediaQuery(
      data: MediaQuery.of(context).copyWith(textScaler: TextScaler.noScaling),
      child: Scaffold(
      backgroundColor: AppColors.paper,
      body: SafeArea(
        bottom: false,
        child: Column(
          children: [
            _TopBar(dirty: dirty),
            Expanded(
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => setState(() => _openDropdown = null),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _Preview(serif: draftSerif, sans: draftSans, size: _draft.size),
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            _FontDropdown(
                              label: '제목 폰트',
                              kind: _DropdownKind.serif,
                              options: kSerifOptions,
                              selectedId: _draft.serifId,
                              isOpen: _openDropdown == 'serif',
                              onToggle: () => setState(() {
                                _openDropdown = _openDropdown == 'serif' ? null : 'serif';
                              }),
                              onSelect: (id) => setState(() {
                                _draft = _draft.copyWith(serifId: id);
                                _openDropdown = null;
                              }),
                            ),
                            const SizedBox(height: 14),
                            _FontDropdown(
                              label: '본문 폰트',
                              kind: _DropdownKind.sans,
                              options: kSansOptions,
                              selectedId: _draft.sansId,
                              isOpen: _openDropdown == 'sans',
                              onToggle: () => setState(() {
                                _openDropdown = _openDropdown == 'sans' ? null : 'sans';
                              }),
                              onSelect: (id) => setState(() {
                                _draft = _draft.copyWith(sansId: id);
                                _openDropdown = null;
                              }),
                            ),
                            const SizedBox(height: 22),
                            _SizeGrid(
                              size: _draft.size,
                              onSelect: (s) => setState(() => _draft = _draft.copyWith(size: s)),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 80),
                    ],
                  ),
                ),
              ),
            ),
            _BottomActions(
              dirty: dirty,
              onReset: () => setState(() {
                _draft = applied;
                _openDropdown = null;
              }),
              onApply: () async {
                final messenger = ScaffoldMessenger.of(context);
                await ref.read(fontSettingsProvider.notifier).apply(_draft);
                if (!mounted) return;
                messenger.showSnackBar(
                  const SnackBar(
                    content: Text('적용됐어요'),
                    duration: Duration(milliseconds: 1400),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    ),
    );
  }
}

class _TopBar extends StatelessWidget {
  final bool dirty;
  const _TopBar({required this.dirty});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
      decoration: const BoxDecoration(
        color: AppColors.paper,
        border: Border(bottom: BorderSide(color: AppColors.ink, width: 2)),
      ),
      child: Row(
        children: [
          IconButton(
            visualDensity: VisualDensity.compact,
            icon: const AppIcon(AppIconName.arrowLeft, size: 22, color: AppColors.ink),
            onPressed: () => context.pop(),
          ),
          const Expanded(
            child: Center(
              child: Text(
                '폰트 설정',
                style: TextStyle(
                  fontFamily: AppFonts.serif,
                  fontSize: 17,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.34,
                  color: AppColors.ink,
                ),
              ),
            ),
          ),
          SizedBox(
            width: 64,
            child: dirty
                ? const Text(
                    '● 변경됨',
                    textAlign: TextAlign.right,
                    style: TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 12,
                      letterSpacing: 1.68,
                      color: AppColors.accent,
                    ),
                  )
                : const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}

class _Preview extends StatelessWidget {
  final FontOption serif;
  final FontOption sans;
  final FontSizeStep size;
  const _Preview({required this.serif, required this.sans, required this.size});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.paper2,
        border: Border(bottom: BorderSide(color: AppColors.line)),
      ),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                const Expanded(
                  child: Text(
                    '미리보기',
                    style: TextStyle(
                      fontFamily: AppFonts.sans,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.68,
                      color: AppColors.ink3,
                    ),
                  ),
                ),
                Text(
                  '${serif.name.replaceAll(RegExp(r' KR$'), '')} / ${sans.name.replaceAll(RegExp(r' KR$'), '')} · ${size.label}',
                  style: const TextStyle(
                    fontFamily: AppFonts.mono,
                    fontSize: 12,
                    letterSpacing: 0.96,
                    color: AppColors.ink4,
                  ),
                ),
              ],
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: AppColors.paper,
              border: Border.all(color: AppColors.line),
            ),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '경제 · 4월 25일',
                  style: TextStyle(
                    fontFamily: sans.family,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2.16,
                    color: AppColors.accent,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '한은 기준금리 동결, 시장은 “하반기 인하” 가능성에 무게',
                  style: TextStyle(
                    fontFamily: serif.family,
                    fontWeight: FontWeight.values[
                        (serif.weight ~/ 100).clamp(1, 9) - 1],
                    fontSize: 22 * size.mult,
                    height: 1.28,
                    letterSpacing: -0.55,
                    color: AppColors.ink,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  '한국은행 금융통화위원회가 기준금리를 연 3.50%로 다섯 차례 연속 동결했다. 다만 의사록에서 일부 위원들이 물가 둔화세를 근거로 연내 인하 가능성을 시사하면서 시장은 7월 회의를 주목하고 있다.',
                  style: TextStyle(
                    fontFamily: sans.family,
                    fontWeight: FontWeight.w500,
                    fontSize: 13 * size.mult,
                    height: 1.65,
                    letterSpacing: -0.07,
                    color: AppColors.ink2,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          const Row(
            children: [
              _PreviewLegend(color: AppColors.accent, label: '제목'),
              SizedBox(width: 16),
              _PreviewLegend(color: AppColors.ink3, label: '본문'),
            ],
          ),
        ],
      ),
    );
  }
}

class _PreviewLegend extends StatelessWidget {
  final Color color;
  final String label;
  const _PreviewLegend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 8, height: 8, color: color),
        const SizedBox(width: 5),
        Text(
          label,
          style: const TextStyle(
            fontFamily: AppFonts.mono,
            fontSize: 12,
            letterSpacing: 1.2,
            color: AppColors.ink3,
          ),
        ),
      ],
    );
  }
}

enum _DropdownKind { serif, sans }

class _FontDropdown extends StatelessWidget {
  final String label;
  final _DropdownKind kind;
  final List<FontOption> options;
  final String selectedId;
  final bool isOpen;
  final VoidCallback onToggle;
  final ValueChanged<String> onSelect;

  const _FontDropdown({
    required this.label,
    required this.kind,
    required this.options,
    required this.selectedId,
    required this.isOpen,
    required this.onToggle,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final current = options.firstWhere((o) => o.id == selectedId,
        orElse: () => options.first);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(
            label,
            style: const TextStyle(
              fontFamily: AppFonts.serif,
              fontSize: 16,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.16,
              color: AppColors.ink,
            ),
          ),
        ),
        InkWell(
          onTap: onToggle,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 120),
            padding: EdgeInsets.symmetric(
              horizontal: isOpen ? 14 : 15,
              vertical: isOpen ? 13 : 14,
            ),
            decoration: BoxDecoration(
              color: AppColors.paper,
              border: Border.all(
                color: AppColors.ink,
                width: isOpen ? 2 : 1,
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        current.name,
                        style: const TextStyle(
                          fontFamily: AppFonts.sans,
                          fontSize: 12,
                          letterSpacing: 0.72,
                          color: AppColors.ink3,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _sampleFor(kind),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontFamily: current.family,
                          fontWeight: FontWeight.values[
                              (current.weight ~/ 100).clamp(1, 9) - 1],
                          fontSize: kind == _DropdownKind.serif ? 20 : 14,
                          height: kind == _DropdownKind.serif ? 1.2 : 1.5,
                          letterSpacing: kind == _DropdownKind.serif ? -0.5 : -0.07,
                          color: AppColors.ink,
                        ),
                      ),
                    ],
                  ),
                ),
                AnimatedRotation(
                  turns: isOpen ? 0.5 : 0,
                  duration: const Duration(milliseconds: 160),
                  child: const AppIcon(AppIconName.chevronDown,
                      size: 18, color: AppColors.ink2),
                ),
              ],
            ),
          ),
        ),
        if (isOpen)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.paper,
                border: Border.all(color: AppColors.line),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x14000000),
                    blurRadius: 18,
                    offset: Offset(0, 6),
                  ),
                ],
              ),
              child: Column(
                children: [
                  for (int i = 0; i < options.length; i++) ...[
                    _DropdownRow(
                      kind: kind,
                      option: options[i],
                      selected: options[i].id == selectedId,
                      onTap: options[i].available
                          ? () => onSelect(options[i].id)
                          : null,
                    ),
                    if (i < options.length - 1)
                      const Divider(height: 1, thickness: 1, color: AppColors.lineSoft),
                  ],
                ],
              ),
            ),
          ),
      ],
    );
  }

  String _sampleFor(_DropdownKind k) => switch (k) {
        _DropdownKind.serif => '제목은 신문처럼',
        _DropdownKind.sans => '본문은 읽기 좋게 가나다 ABC 0123',
      };
}

class _DropdownRow extends StatelessWidget {
  final _DropdownKind kind;
  final FontOption option;
  final bool selected;
  final VoidCallback? onTap;

  const _DropdownRow({
    required this.kind,
    required this.option,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final disabled = onTap == null;
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 12),
        color: selected ? AppColors.paper2 : Colors.transparent,
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        option.name,
                        style: TextStyle(
                          fontFamily: AppFonts.sans,
                          fontSize: 12,
                          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                          color: disabled ? AppColors.ink4 : AppColors.ink,
                        ),
                      ),
                      if (disabled) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.lineSoft,
                            borderRadius: BorderRadius.circular(AppRadius.sm),
                          ),
                          child: const Text(
                            '준비 중',
                            style: TextStyle(
                              fontFamily: AppFonts.mono,
                              fontSize: 12,
                              letterSpacing: 0.96,
                              color: AppColors.ink3,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    kind == _DropdownKind.serif
                        ? '제목은 신문처럼'
                        : '본문은 읽기 좋게 가나다 ABC 0123',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontFamily: option.family,
                      fontWeight: FontWeight.values[
                          (option.weight ~/ 100).clamp(1, 9) - 1],
                      fontSize: kind == _DropdownKind.serif ? 18 : 13,
                      letterSpacing: kind == _DropdownKind.serif ? -0.45 : -0.07,
                      color: disabled ? AppColors.ink4 : AppColors.ink2,
                    ),
                  ),
                ],
              ),
            ),
            if (selected)
              const AppIcon(AppIconName.check, size: 16, color: AppColors.ink),
          ],
        ),
      ),
    );
  }
}

class _SizeGrid extends StatelessWidget {
  final FontSizeStep size;
  final ValueChanged<FontSizeStep> onSelect;
  const _SizeGrid({required this.size, required this.onSelect});

  @override
  Widget build(BuildContext context) {
    final values = FontSizeStep.values;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              const Expanded(
                child: Text(
                  '글자 크기',
                  style: TextStyle(
                    fontFamily: AppFonts.serif,
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.16,
                    color: AppColors.ink,
                  ),
                ),
              ),
              Text(
                '${(size.mult * 100).round()}%',
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  letterSpacing: 1.2,
                  color: AppColors.ink4,
                ),
              ),
            ],
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: AppColors.paper,
            border: Border.all(color: AppColors.line),
          ),
          child: Row(
            children: [
              for (int i = 0; i < values.length; i++)
                Expanded(
                  child: _SizeCell(
                    step: values[i],
                    index: i,
                    selected: values[i] == size,
                    showRightDivider: i < values.length - 1,
                    onTap: () => onSelect(values[i]),
                  ),
                ),
            ],
          ),
        ),
        const Padding(
          padding: EdgeInsets.only(top: 8),
          child: Text(
            '제목과 본문 글자가 동시에 조절됩니다.',
            style: TextStyle(
              fontFamily: AppFonts.sans,
              fontSize: 12,
              height: 1.5,
              color: AppColors.ink3,
            ),
          ),
        ),
      ],
    );
  }
}

class _SizeCell extends StatelessWidget {
  final FontSizeStep step;
  final int index;
  final bool selected;
  final bool showRightDivider;
  final VoidCallback onTap;
  const _SizeCell({
    required this.step,
    required this.index,
    required this.selected,
    required this.showRightDivider,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.fromLTRB(0, 12, 0, 14),
        decoration: BoxDecoration(
          color: selected ? AppColors.ink : Colors.transparent,
          border: showRightDivider
              ? const Border(right: BorderSide(color: AppColors.line))
              : null,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '가',
              style: TextStyle(
                fontFamily: AppFonts.serif,
                fontWeight: selected ? FontWeight.w900 : FontWeight.w700,
                fontSize: 12.0 + (index * 3),
                height: 1,
                letterSpacing: -0.24,
                color: selected ? AppColors.paper : AppColors.ink2,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              step.label,
              style: TextStyle(
                fontFamily: AppFonts.sans,
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                fontSize: 12,
                color: selected ? AppColors.paper : AppColors.ink2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BottomActions extends StatelessWidget {
  final bool dirty;
  final VoidCallback onReset;
  final VoidCallback onApply;
  const _BottomActions({
    required this.dirty,
    required this.onReset,
    required this.onApply,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.paper,
        border: Border(top: BorderSide(color: AppColors.line)),
      ),
      padding: EdgeInsets.fromLTRB(
        20, 12, 20, 14 + MediaQuery.viewPaddingOf(context).bottom,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 132,
            child: OutlinedButton(
              onPressed: dirty ? onReset : null,
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 13),
                side: const BorderSide(color: AppColors.line),
                foregroundColor: dirty ? AppColors.ink : AppColors.ink4,
                shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.all(Radius.circular(AppRadius.sm)),
                ),
              ),
              child: const Text(
                '되돌리기',
                style: TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  letterSpacing: -0.14,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: FilledButton(
              onPressed: dirty ? onApply : null,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 13),
                backgroundColor: dirty ? AppColors.ink : AppColors.line,
                foregroundColor: dirty ? AppColors.paper : AppColors.ink4,
                disabledBackgroundColor: AppColors.line,
                disabledForegroundColor: AppColors.ink4,
                shape: const RoundedRectangleBorder(
                  borderRadius: BorderRadius.all(Radius.circular(AppRadius.sm)),
                ),
              ),
              child: Text(
                dirty ? '적용하기' : '적용됨',
                style: const TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  letterSpacing: -0.14,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
