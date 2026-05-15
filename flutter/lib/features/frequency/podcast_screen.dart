import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_icons.dart';
import '../../core/theme/app_theme.dart';
import '../../shared/models/episode.dart';
import '../../shared/models/headline_topic.dart';
import '../../shared/widgets/async_state_views.dart';
import '../today/data/headlines_repository.dart';
import 'audio_controller.dart';
import 'data/podcast_repository.dart';

/// 오늘의 팟캐스트 — Supabase `podcasts` 테이블 기반.
class PodcastScreen extends ConsumerStatefulWidget {
  const PodcastScreen({super.key});

  @override
  ConsumerState<PodcastScreen> createState() => _PodcastScreenState();
}

class _PodcastScreenState extends ConsumerState<PodcastScreen> {
  Episode? _override; // 사용자가 리스트에서 탭한 에피소드

  @override
  Widget build(BuildContext context) {
    final currentAsync = ref.watch(currentEpisodeProvider);
    final recentAsync = ref.watch(recentEpisodesProvider);

    final selected = _override ?? currentAsync.valueOrNull;

    return Container(
      color: AppColors.paper,
      child: SafeArea(
        bottom: false,
        child: Column(
          children: [
            Expanded(
              child: RefreshIndicator(
                onRefresh: () async {
                  ref.invalidate(currentEpisodeProvider);
                  ref.invalidate(recentEpisodesProvider);
                },
                color: AppColors.ink,
                child: currentAsync.when(
                  loading: () => const _PodcastLoading(),
                  error: (e, _) => CenteredScrollable(
                    child: EditorialError(
                      error: e,
                      onRetry: () =>
                          ref.invalidate(currentEpisodeProvider),
                    ),
                  ),
                  data: (ep) => ListView(
                    padding: EdgeInsets.zero,
                    children: [
                      if (selected == null)
                        const EditorialEmpty(
                          icon: Icons.podcasts_outlined,
                          message: '아직 팟캐스트가 없어요.\n오전 브리핑이 곧 올라옵니다.',
                        )
                      else ...[
                        _AlbumArt(episode: selected),
                        _PlayerBlock(episode: selected),
                        _BriefingNews(episode: selected),
                      ],
                      recentAsync.when(
                        loading: () => const SizedBox.shrink(),
                        error: (_, _) => const SizedBox.shrink(),
                        data: (recent) => _RecentEpisodes(
                          episodes: recent.take(6).toList(),
                          currentId: selected?.id,
                          onSelect: (e) => setState(() => _override = e),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AlbumArt extends StatelessWidget {
  final Episode episode;
  const _AlbumArt({required this.episode});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 180,
      color: AppColors.ink,
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 6, height: 6,
                    decoration: const BoxDecoration(
                      color: AppColors.accent, shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '${episode.slot.code} · 오늘의 팟캐스트',
                    style: const TextStyle(
                      fontFamily: AppFonts.mono,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.44,
                      color: AppColors.accent,
                    ),
                  ),
                ],
              ),
              Text(
                '${episode.dateKo} · ${episode.slot.ko}',
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  letterSpacing: 0.48,
                  color: Color(0xE6F7F2E9),
                ),
              ),
            ],
          ),
          const Spacer(),
          const Text(
            '오늘의 팟캐스트',
            style: TextStyle(
              fontFamily: AppFonts.serif,
              fontSize: 36,
              fontWeight: FontWeight.w900,
              letterSpacing: -1.1,
              height: 1,
              color: AppColors.paper,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '${episode.dateKo} · ${episode.slot.ko} 브리핑',
            style: const TextStyle(
              fontFamily: AppFonts.serif,
              fontSize: 14,
              color: Color(0xE6F7F2E9),
            ),
          ),
        ],
      ),
    );
  }
}

class _PlayerBlock extends ConsumerWidget {
  final Episode episode;
  const _PlayerBlock({required this.episode});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(audioControllerProvider);
    final controller = ref.read(audioControllerProvider.notifier);
    final isCurrent = state.episode?.id == episode.id;
    final hasAudio = episode.audioPath != null;

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 18, 24, 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (episode.title != null && episode.title!.isNotEmpty)
            Text(
              episode.title!,
              style: const TextStyle(
                fontFamily: AppFonts.serif,
                fontSize: 18,
                fontWeight: FontWeight.w800,
                height: 1.35,
                letterSpacing: -0.36,
                color: AppColors.ink,
              ),
            ),
          const SizedBox(height: 14),
          _Progress(
            progress: isCurrent ? state.progress : 0,
            positionLabel: isCurrent ? _fmtDuration(state.position) : '00:00',
            totalLabel: isCurrent
                ? (state.duration != null ? _fmtDuration(state.duration!) : '—:—')
                : '—:—',
          ),
          const SizedBox(height: 20),
          _Controls(
            isCurrent: isCurrent,
            playing: isCurrent && state.playing,
            loading: isCurrent && state.loading,
            hasAudio: hasAudio,
            speed: state.speed,
            onPlayPause: () => hasAudio ? controller.play(episode) : null,
            onSeekBack: () =>
                isCurrent ? controller.skip(const Duration(seconds: -10)) : null,
            onSeekFwd: () =>
                isCurrent ? controller.skip(const Duration(seconds: 10)) : null,
            onSpeed: controller.cycleSpeed,
            onList: () => context.push('/episodes'),
          ),
          if (!hasAudio)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Text(
                '오디오가 아직 준비되지 않았어요.',
                style: TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 12,
                  color: AppColors.ink3,
                ),
              ),
            ),
          if (isCurrent && state.error != null)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Text(
                '${state.error}',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontFamily: AppFonts.sans,
                  fontSize: 12,
                  color: AppColors.accent,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _Progress extends StatelessWidget {
  final double progress;
  final String positionLabel;
  final String totalLabel;

  const _Progress({
    required this.progress,
    required this.positionLabel,
    required this.totalLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(2),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 3,
            backgroundColor: AppColors.line,
            valueColor: const AlwaysStoppedAnimation(AppColors.ink),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              positionLabel,
              style: const TextStyle(
                fontFamily: AppFonts.mono,
                fontSize: 12,
                letterSpacing: 0.72,
                color: AppColors.ink3,
              ),
            ),
            Text(
              totalLabel,
              style: const TextStyle(
                fontFamily: AppFonts.mono,
                fontSize: 12,
                letterSpacing: 0.72,
                color: AppColors.ink3,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _Controls extends StatelessWidget {
  final bool isCurrent;
  final bool playing;
  final bool loading;
  final bool hasAudio;
  final double speed;
  final VoidCallback? onPlayPause;
  final VoidCallback? onSeekBack;
  final VoidCallback? onSeekFwd;
  final VoidCallback onSpeed;
  final VoidCallback onList;

  const _Controls({
    required this.isCurrent,
    required this.playing,
    required this.loading,
    required this.hasAudio,
    required this.speed,
    required this.onPlayPause,
    required this.onSeekBack,
    required this.onSeekFwd,
    required this.onSpeed,
    required this.onList,
  });

  @override
  Widget build(BuildContext context) {
    final playIcon = loading
        ? const SizedBox(
            width: 22, height: 22,
            child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.paper),
          )
        : Icon(
            playing ? Icons.pause_rounded : Icons.play_arrow_rounded,
            color: AppColors.paper,
            size: 32,
          );

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        _PillButton(label: '${speed.toStringAsFixed(1)}×', onTap: onSpeed),
        IconButton(
          icon: const AppIcon(AppIconName.skipBack, size: 26),
          onPressed: onSeekBack,
        ),
        Container(
          width: 64, height: 64,
          decoration: BoxDecoration(
            color: hasAudio ? AppColors.ink : AppColors.ink4,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            icon: playIcon,
            onPressed: hasAudio ? onPlayPause : null,
          ),
        ),
        IconButton(
          icon: const AppIcon(AppIconName.skipFwd, size: 26),
          onPressed: onSeekFwd,
        ),
        _PillIconButton(icon: AppIconName.list, onTap: onList),
      ],
    );
  }
}

class _PillButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _PillButton({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.pill),
      child: Container(
        constraints: const BoxConstraints(minHeight: 32, minWidth: 48),
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          border: Border.all(color: AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: Text(
          label,
          style: const TextStyle(
            fontFamily: AppFonts.mono,
            fontSize: 12,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.96,
            color: AppColors.ink3,
          ),
        ),
      ),
    );
  }
}

class _PillIconButton extends StatelessWidget {
  final AppIconName icon;
  final VoidCallback onTap;
  const _PillIconButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.pill),
      child: Container(
        constraints: const BoxConstraints(minHeight: 32, minWidth: 48),
        alignment: Alignment.center,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          border: Border.all(color: AppColors.line),
          borderRadius: BorderRadius.circular(AppRadius.pill),
        ),
        child: AppIcon(icon, size: 14, color: AppColors.ink3),
      ),
    );
  }
}

/// 팟캐스트 전용 로딩 — 검은 앨범아트 스켈레톤 + 7-bar 이퀄라이저 + 컨트롤 스켈레톤.
/// 로드 후 화면과 같은 윤곽을 미리 잡아서 레이아웃 점프를 없앤다.
class _PodcastLoading extends StatefulWidget {
  const _PodcastLoading();

  @override
  State<_PodcastLoading> createState() => _PodcastLoadingState();
}

class _PodcastLoadingState extends State<_PodcastLoading>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.zero,
      physics: const AlwaysScrollableScrollPhysics(),
      children: [
        const _AlbumArtSkeleton(),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 28, 24, 12),
          child: Column(
            children: [
              _Equalizer(controller: _controller),
              const SizedBox(height: 18),
              Text(
                '오늘의 브리핑을 불러오는 중',
                style: TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  letterSpacing: 1.68,
                  color: AppColors.ink3,
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: const [
              _SkeletonBar(width: double.infinity, height: 18),
              SizedBox(height: 18),
              _SkeletonBar(width: double.infinity, height: 3),
              SizedBox(height: 28),
              _SkeletonControls(),
            ],
          ),
        ),
      ],
    );
  }
}

/// 검은 앨범아트 패널 — 실제 [_AlbumArt] 와 같은 180px 높이 / 같은 패딩.
/// 작은 액센트 점 + mono 캡션은 동일하게 출력하고, serif 제목/날짜 자리는 스켈레톤 바.
class _AlbumArtSkeleton extends StatelessWidget {
  const _AlbumArtSkeleton();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 180,
      color: AppColors.ink,
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 6, height: 6,
                decoration: const BoxDecoration(
                  color: AppColors.accent, shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '오늘의 팟캐스트',
                style: TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1.44,
                  color: AppColors.accent,
                ),
              ),
            ],
          ),
          const Spacer(),
          Container(
            width: 220, height: 30,
            decoration: BoxDecoration(
              color: AppColors.paper.withValues(alpha: 0.18),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 10),
          Container(
            width: 140, height: 12,
            decoration: BoxDecoration(
              color: AppColors.paper.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ],
      ),
    );
  }
}

/// sin wave + 위상 오프셋으로 자연스럽게 위아래 움직이는 7개 막대.
/// 색은 ink 단색 — 그라디언트나 글로우 없이 에디토리얼 톤 유지.
/// AnimatedBuilder 는 막대마다 따로 두어, Row/SizedBox 등 정적 자식이 매 프레임
/// 리빌드되지 않도록 한다.
class _Equalizer extends StatelessWidget {
  final AnimationController controller;
  const _Equalizer({required this.controller});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 56,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          for (int i = 0; i < 7; i++) ...[
            if (i > 0) const SizedBox(width: 5),
            _EqualizerBar(controller: controller, phaseOffset: i * 0.55),
          ],
        ],
      ),
    );
  }
}

class _EqualizerBar extends StatelessWidget {
  final AnimationController controller;
  final double phaseOffset;
  const _EqualizerBar({required this.controller, required this.phaseOffset});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (_, _) {
        final phase = controller.value * 2 * math.pi + phaseOffset;
        final v = (math.sin(phase) + 1) / 2; // 0..1
        final h = 14 + v * 38;                // 14..52
        return Container(
          width: 4,
          height: h,
          decoration: BoxDecoration(
            color: AppColors.ink,
            borderRadius: BorderRadius.circular(2),
          ),
        );
      },
    );
  }
}

class _SkeletonBar extends StatelessWidget {
  final double width;
  final double height;
  const _SkeletonBar({required this.width, required this.height});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppColors.paper2,
        border: Border.all(color: AppColors.line),
        borderRadius: BorderRadius.circular(2),
      ),
    );
  }
}

class _SkeletonControls extends StatelessWidget {
  const _SkeletonControls();

  @override
  Widget build(BuildContext context) {
    Widget pill() => Container(
      width: 56, height: 32,
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.line),
        borderRadius: BorderRadius.circular(AppRadius.pill),
      ),
    );
    Widget seek() => Container(
      width: 26, height: 26,
      decoration: BoxDecoration(
        color: AppColors.paper2,
        borderRadius: BorderRadius.circular(13),
      ),
    );

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        pill(),
        seek(),
        Container(
          width: 64, height: 64,
          decoration: const BoxDecoration(
            color: AppColors.ink4,
            shape: BoxShape.circle,
          ),
        ),
        seek(),
        pill(),
      ],
    );
  }
}

class _RecentEpisodes extends StatelessWidget {
  final List<Episode> episodes;
  final String? currentId;
  final ValueChanged<Episode> onSelect;

  const _RecentEpisodes({
    required this.episodes,
    required this.currentId,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    if (episodes.isEmpty) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.only(bottom: 10),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.line)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '최근 에피소드',
                  style: TextStyle(
                    fontFamily: AppFonts.mono,
                    fontSize: 12,
                    letterSpacing: 1.68,
                    color: AppColors.ink3,
                  ),
                ),
                Builder(
                  builder: (ctx) => GestureDetector(
                    onTap: () => ctx.push('/episodes'),
                    child: Text(
                      '전체 ›',
                      style: TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 13,
                        color: AppColors.ink3,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          for (int i = 0; i < episodes.length; i++)
            _EpisodeRow(
              ep: episodes[i],
              current: episodes[i].id == currentId,
              onTap: () => onSelect(episodes[i]),
              showDivider: i < episodes.length - 1,
            ),
        ],
      ),
    );
  }
}

class _EpisodeRow extends StatelessWidget {
  final Episode ep;
  final bool current;
  final VoidCallback onTap;
  final bool showDivider;

  const _EpisodeRow({
    required this.ep,
    required this.current,
    required this.onTap,
    required this.showDivider,
  });

  @override
  Widget build(BuildContext context) {
    final upcoming = ep.audioPath == null;

    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          border: showDivider
              ? const Border(bottom: BorderSide(color: AppColors.lineSoft))
              : null,
        ),
        child: Opacity(
          opacity: upcoming ? 0.55 : 1,
          child: Row(
            children: [
              _Tile(ep: ep, current: current, upcoming: upcoming),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          '${ep.dateKo} ${ep.slot.ko}',
                          style: TextStyle(
                            fontFamily: AppFonts.serif,
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                            color: current ? AppColors.accent : AppColors.ink,
                          ),
                        ),
                        if (current) ...[
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
                        fontSize: 12,
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
              if (current)
                const AppIcon(AppIconName.volume, size: 18, color: AppColors.accent)
              else if (upcoming)
                const AppIcon(AppIconName.bell, size: 16, color: AppColors.ink4)
              else
                const AppIcon(AppIconName.play, size: 16, color: AppColors.ink3),
            ],
          ),
        ),
      ),
    );
  }
}

class _Tile extends StatelessWidget {
  final Episode ep;
  final bool current;
  final bool upcoming;
  const _Tile({required this.ep, required this.current, required this.upcoming});

  @override
  Widget build(BuildContext context) {
    final bg = current
        ? AppColors.accent
        : (upcoming ? AppColors.paper2 : AppColors.ink);
    final fg = upcoming ? AppColors.ink3 : AppColors.paper;

    return Container(
      width: 44, height: 44,
      decoration: BoxDecoration(
        color: bg,
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
              color: upcoming ? AppColors.ink3 : fg.withValues(alpha: 0.75),
            ),
          ),
          const SizedBox(height: 2),
          Text(
            ep.slot.code,
            style: TextStyle(
              fontFamily: AppFonts.serif,
              fontWeight: FontWeight.w900,
              fontSize: 13,
              height: 1,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}

/// 이 브리핑이 다룬 뉴스 — podcast.jsx v2.1 B 변형의 "이 브리핑의 뉴스" 섹션.
/// 선택된 에피소드의 date+slot 으로 `todayHeadlinesProvider` 를 구독.
class _BriefingNews extends ConsumerWidget {
  final Episode episode;
  const _BriefingNews({required this.episode});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final args = (
      date: DateTime(episode.date.year, episode.date.month, episode.date.day),
      slot: episode.slot.code,
    );
    final async = ref.watch(todayHeadlinesProvider(args));

    return async.when(
      loading: () => const SizedBox.shrink(),
      error: (_, _) => const SizedBox.shrink(),
      data: (topics) {
        if (topics.isEmpty) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 18, 24, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.only(bottom: 8),
                decoration: const BoxDecoration(
                  border: Border(bottom: BorderSide(color: AppColors.line)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '이 브리핑의 뉴스',
                      style: TextStyle(
                        fontFamily: AppFonts.serif,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.14,
                        color: AppColors.accent,
                      ),
                    ),
                    Text(
                      '${topics.length}개',
                      style: const TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 12,
                        color: AppColors.ink3,
                      ),
                    ),
                  ],
                ),
              ),
              for (int i = 0; i < topics.length; i++)
                _BriefingNewsRow(
                  topic: topics[i],
                  index: i,
                  showDivider: i < topics.length - 1,
                ),
            ],
          ),
        );
      },
    );
  }
}

class _BriefingNewsRow extends StatelessWidget {
  final HeadlineTopic topic;
  final int index;
  final bool showDivider;

  const _BriefingNewsRow({
    required this.topic,
    required this.index,
    required this.showDivider,
  });

  @override
  Widget build(BuildContext context) {
    final cat = topic.category;
    return InkWell(
      onTap: topic.representativeNewsId.isEmpty
          ? null
          : () => context.push(
              '/news/${Uri.encodeComponent(topic.representativeNewsId)}'),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          border: showDivider
              ? const Border(bottom: BorderSide(color: AppColors.lineSoft))
              : null,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 28,
              child: Text(
                (index + 1).toString().padLeft(2, '0'),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: AppFonts.mono,
                  fontSize: 12,
                  letterSpacing: 0.96,
                  color: AppColors.ink4,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: cat.color,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        cat.ko,
                        style: const TextStyle(
                          fontFamily: AppFonts.mono,
                          fontSize: 12,
                          letterSpacing: 0.96,
                          color: AppColors.ink3,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '· 관련 보도 ${topic.clusterSize}건',
                        style: const TextStyle(
                          fontFamily: AppFonts.mono,
                          fontSize: 12,
                          color: AppColors.ink4,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    topic.headline,
                    style: const TextStyle(
                      fontFamily: AppFonts.serif,
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      height: 1.35,
                      letterSpacing: -0.16,
                      color: AppColors.ink,
                    ),
                  ),
                  if (topic.summary.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Text(
                      topic.summary,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontFamily: AppFonts.sans,
                        fontSize: 13,
                        height: 1.5,
                        color: AppColors.ink3,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            const AppIcon(
              AppIconName.chevronRight,
              size: 14,
              color: AppColors.ink4,
            ),
          ],
        ),
      ),
    );
  }
}

String _fmtDuration(Duration d) {
  String two(int n) => n.toString().padLeft(2, '0');
  final h = d.inHours;
  final m = d.inMinutes.remainder(60);
  final s = d.inSeconds.remainder(60);
  if (h > 0) return '$h:${two(m)}:${two(s)}';
  return '${two(m)}:${two(s)}';
}
