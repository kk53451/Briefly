import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';

import '../../shared/models/episode.dart';
import 'data/podcast_repository.dart';

/// 플레이어 표면 상태. Flutter UI 바인딩에 필요한 최소 정보만 노출.
class AudioState {
  final Episode? episode;
  final bool playing;
  final Duration position;
  final Duration? duration;
  final double speed;
  final bool loading;
  final Object? error;

  const AudioState({
    required this.episode,
    required this.playing,
    required this.position,
    required this.duration,
    required this.speed,
    required this.loading,
    required this.error,
  });

  static const initial = AudioState(
    episode: null,
    playing: false,
    position: Duration.zero,
    duration: null,
    speed: 1.0,
    loading: false,
    error: null,
  );

  AudioState copyWith({
    Episode? episode,
    bool? playing,
    Duration? position,
    Duration? duration,
    double? speed,
    bool? loading,
    Object? error,
    bool clearError = false,
    bool clearDuration = false,
  }) {
    return AudioState(
      episode: episode ?? this.episode,
      playing: playing ?? this.playing,
      position: position ?? this.position,
      duration: clearDuration ? null : (duration ?? this.duration),
      speed: speed ?? this.speed,
      loading: loading ?? this.loading,
      error: clearError ? null : (error ?? this.error),
    );
  }

  double get progress {
    final d = duration;
    if (d == null || d.inMilliseconds == 0) return 0;
    return (position.inMilliseconds / d.inMilliseconds).clamp(0.0, 1.0);
  }
}

class AudioController extends StateNotifier<AudioState> {
  AudioController(this._ref) : super(AudioState.initial) {
    _player.playerStateStream.listen((s) {
      state = state.copyWith(
        playing: s.playing,
        loading: s.processingState == ProcessingState.loading ||
            s.processingState == ProcessingState.buffering,
      );
    });
    _player.positionStream.listen((p) {
      state = state.copyWith(position: p);
    });
    _player.durationStream.listen((d) {
      if (d != null) {
        state = state.copyWith(duration: d);
      }
    });
  }

  final Ref _ref;
  final AudioPlayer _player = AudioPlayer();

  /// 주어진 에피소드를 로드하고 재생 시작. 현재 에피소드와 같으면 toggle.
  Future<void> play(Episode ep) async {
    if (state.episode?.id == ep.id && _player.audioSource != null) {
      if (_player.playing) {
        await _player.pause();
      } else {
        await _player.play();
      }
      return;
    }

    final repo = _ref.read(podcastRepositoryProvider);
    final url = repo.publicUrl(ep.audioPath);
    if (url == null) {
      state = state.copyWith(
        episode: ep, error: '오디오가 아직 준비되지 않았어요', loading: false,
      );
      return;
    }

    state = state.copyWith(
      episode: ep,
      loading: true,
      clearError: true,
      position: Duration.zero,
      clearDuration: true,
    );

    try {
      await _player.setAudioSource(
        AudioSource.uri(
          Uri.parse(url),
          tag: MediaItem(
            id: ep.id,
            album: 'Briefly',
            title: ep.displayTitle,
            displayTitle: ep.displayTitle,
            displaySubtitle: '${ep.dateKo} · ${ep.slot.ko} 브리핑',
          ),
        ),
      );
      await _player.play();
    } catch (e) {
      state = state.copyWith(error: e, loading: false);
    }
  }

  Future<void> togglePlay() async {
    if (_player.playing) {
      await _player.pause();
    } else {
      await _player.play();
    }
  }

  Future<void> seek(Duration pos) => _player.seek(pos);
  Future<void> seekFraction(double f) {
    final d = state.duration;
    if (d == null) return Future.value();
    return _player.seek(d * f.clamp(0.0, 1.0));
  }

  Future<void> skip(Duration delta) async {
    final target = state.position + delta;
    final d = state.duration;
    final bounded = d == null
        ? target
        : (target.isNegative
            ? Duration.zero
            : (target > d ? d : target));
    await _player.seek(bounded);
  }

  Future<void> cycleSpeed() async {
    const speeds = [1.0, 1.2, 1.5, 2.0, 0.75];
    final idx = speeds.indexOf(state.speed);
    final next = speeds[(idx + 1) % speeds.length];
    await _player.setSpeed(next);
    state = state.copyWith(speed: next);
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}

final audioControllerProvider =
    StateNotifierProvider<AudioController, AudioState>(
  (ref) => AudioController(ref),
);
