import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/episode.dart';
import '../../shared/widgets/async_state_views.dart';
import 'audio_controller.dart';
import 'data/podcast_repository.dart';

/// "오늘의 팟캐스트" 카탈로그 — 날짜별 그룹 + AM/PM 필터.
class EpisodesScreen extends ConsumerStatefulWidget {
  const EpisodesScreen({super.key});

  @override
  ConsumerState<EpisodesScreen> createState() => _EpisodesScreenState();
}

enum _Filter { all, am, pm, saved }

extension on _Filter {
  String get label {
    switch (this) {
      case _Filter.all:   return '전체';
      case _Filter.am:    return '오전 AM';
      case _Filter.pm:    return '오후 PM';
      case _Filter.saved: return '저장됨';
    }
  }
}

class _EpisodesScreenState extends ConsumerState<EpisodesScreen> {
  _Filter _filter = _Filter.all;

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(recentEpisodesProvider);

    return Scaffold(
      backgroundColor: AppColors.paper,
      body: SafeArea(
        child: Column(
          children: [
            _Header(),
            _FilterBar(
              current: _filter,
              onSelected: (f) => setState(() => _filter = f),
            ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async => ref.invalidate(recentEpisodesProvider),
                color: AppColors.ink,
                child: async.when(
                  loading: () => const EditorialLoading(height: 300),
                  error: (e, _) => ListView(
                    children: [
                      EditorialError(
                        error: e,
                        onRetry: () =>
                            ref.invalidate(recentEpisodesProvider),
                      ),
                    ],
                  ),
                  data: (list) {
                    final filtered = _apply(list, _filter);
                    if (filtered.isEmpty) {
                      return ListView(
                        children: const [
                          EditorialEmpty(message: '해당 조건의 에피소드가 없어요.'),
                        ],
                      );
                    }
                    final groups = _groupByDate(filtered);
                    return ListView.builder(
                      itemCount: groups.length + 1,
                      itemBuilder: (_, i) {
                        if (i == groups.length) return const _LoadMore();
                        return _DateGroup(group: groups[i], index: i);
                      },
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  List<Episode> _apply(List<Episode> list, _Filter f) {
    switch (f) {
      case _Filter.all:   return list;
      case _Filter.am:    return list.where((e) => e.slot == PodcastSlot.am).toList();
      case _Filter.pm:    return list.where((e) => e.slot == PodcastSlot.pm).toList();
      case _Filter.saved: return const []; // TODO: 저장 기능 연동
    }
  }

  List<_Group> _groupByDate(List<Episode> eps) {
    final map = <String, _Group>{};
    for (final e in eps) {
      final key = e.dateShort;
      map.putIfAbsent(
        key,
        () => _Group(dateShort: e.dateShort, dateKo: e.dateKo, day: e.dayShort, eps: []),
      ).eps.add(e);
    }
    return map.values.toList();
  }
}

class _Group {
  final String dateShort;
  final String dateKo;
  final String day;
  final List<Episode> eps;
  _Group({required this.dateShort, required this.dateKo, required this.day, required this.eps});
}

class _Header extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(24, 14, 24, 12),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.ink, width: 2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left_rounded, size: 22),
            onPressed: () => context.pop(),
          ),
          const Text(
            '팟캐스트 목록',
            style: TextStyle(
              fontFamily: AppFonts.serif,
              fontSize: 17,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.34,
            ),
          ),
          const IconButton(
            icon: AppIcon(AppIconName.search, size: 20, color: AppColors.ink3),
            onPressed: null,
          ),
        ],
      ),
    );
  }
}

class _FilterBar extends StatelessWidget {
  final _Filter current;
  final ValueChanged<_Filter> onSelected;
  const _FilterBar({required this.current, required this.onSelected});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.line)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
        child: Row(
          children: [
            for (final f in _Filter.values) ...[
              _Chip(label: f.label, active: current == f, onTap: () => onSelected(f)),
              const SizedBox(width: 6),
            ],
          ],
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _Chip({required this.label, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        constraints: const BoxConstraints(minHeight: 32),
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: active ? AppColors.ink : Colors.transparent,
          border: Border.all(color: active ? AppColors.ink : AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontFamily: AppFonts.sans,
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: active ? AppColors.paper : AppColors.ink2,
          ),
        ),
      ),
    );
  }
}

class _DateGroup extends ConsumerWidget {
  final _Group group;
  final int index;
  const _DateGroup({required this.group, required this.index});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final label = switch (index) { 0 => '오늘', 1 => '어제', _ => null };
    final playing = ref.watch(audioControllerProvider).episode?.id;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 6),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    label ?? '${group.dateKo} (${group.day})',
                    style: const TextStyle(
                      fontFamily: AppFonts.serif,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                      letterSpacing: -0.36,
                    ),
                  ),
                  if (label != null) ...[
                    const SizedBox(width: 8),
                    Text(
                      '${group.dateKo} ${group.day}',
                      style: const TextStyle(
                        fontFamily: AppFonts.mono,
                        fontSize: 12,
                        color: AppColors.ink3,
                      ),
                    ),
                  ],
                ],
              ),
              Text(
                '${group.eps.length}편',
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  color: AppColors.ink3,
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            children: [
              for (final e in group.eps)
                _Row(ep: e, playingId: playing),
            ],
          ),
        ),
      ],
    );
  }
}

class _Row extends ConsumerWidget {
  final Episode ep;
  final String? playingId;
  const _Row({required this.ep, required this.playingId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final upcoming = ep.audioPath == null;
    final playing = playingId == ep.id;

    final tileBg = playing
        ? AppColors.accent
        : (upcoming ? AppColors.paper2 : AppColors.ink);
    final tileFg = upcoming ? AppColors.ink3 : AppColors.paper;

    return InkWell(
      onTap: upcoming
          ? null
          : () => ref.read(audioControllerProvider.notifier).play(ep),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: AppColors.lineSoft)),
        ),
        child: Opacity(
          opacity: upcoming ? 0.5 : 1,
          child: Row(
            children: [
              Container(
                width: 48, height: 48,
                decoration: BoxDecoration(
                  color: tileBg,
                  borderRadius: BorderRadius.circular(AppRadius.sm),
                  border: upcoming ? Border.all(color: AppColors.ink4) : null,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      ep.dateShort,
                      style: TextStyle(
                        fontFamily: AppFonts.mono,
                        fontSize: 11,
                        height: 1.1,
                        letterSpacing: 1.1,
                        color: upcoming ? AppColors.ink3 : tileFg.withValues(alpha: 0.8),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      ep.slot.code,
                      style: TextStyle(
                        fontFamily: AppFonts.serif,
                        fontWeight: FontWeight.w900,
                        fontSize: 14,
                        height: 1,
                        color: tileFg,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '${ep.slot.ko} 브리핑',
                          style: TextStyle(
                            fontFamily: AppFonts.serif,
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: playing ? AppColors.accent : AppColors.ink,
                          ),
                        ),
                        if (playing) ...[
                          const SizedBox(width: 6),
                          Text(
                            '●',
                            style: TextStyle(
                              fontFamily: AppFonts.mono,
                              fontSize: 12,
                              color: AppColors.accent,
                            ),
                          ),
                        ],
                        if (upcoming) ...[
                          const SizedBox(width: 6),
                          Text(
                            '예정',
                            style: TextStyle(
                              fontFamily: AppFonts.mono,
                              fontSize: 12,
                              letterSpacing: 0.96,
                              color: AppColors.ink3,
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      ep.title ?? '제목 미정',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 13,
                        color: AppColors.ink3,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      upcoming ? '발행 예정' : ep.durationLabel,
                      style: const TextStyle(
                        fontFamily: AppFonts.mono,
                        fontSize: 12,
                        letterSpacing: 0.48,
                        color: AppColors.ink4,
                      ),
                    ),
                  ],
                ),
              ),
              if (upcoming)
                const AppIcon(AppIconName.bell, size: 16, color: AppColors.ink4)
              else if (playing)
                const AppIcon(AppIconName.volume, size: 18, color: AppColors.accent)
              else
                const AppIcon(AppIconName.play, size: 16, color: AppColors.ink3),
            ],
          ),
        ),
      ),
    );
  }
}

class _LoadMore extends StatelessWidget {
  const _LoadMore();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 30),
      child: Center(
        child: OutlinedButton(
          onPressed: () {},
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: AppColors.line),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          ),
          child: Text(
            '더 불러오기',
            style: TextStyle(
              fontFamily: AppFonts.mono,
              fontSize: 12,
              letterSpacing: 1.2,
              color: AppColors.ink3,
            ),
          ),
        ),
      ),
    );
  }
}
