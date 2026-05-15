import 'package:intl/intl.dart';

/// "오늘의 팟캐스트" 한 회차.
/// DB: `public.podcasts` (UNIQUE(date, slot)). 정치·경제·국제 통합 10~15분.
enum PodcastSlot { am, pm }

extension PodcastSlotX on PodcastSlot {
  String get code => this == PodcastSlot.am ? 'AM' : 'PM';
  String get ko   => this == PodcastSlot.am ? '오전' : '오후';

  static PodcastSlot fromCode(String code) =>
      code.toUpperCase() == 'PM' ? PodcastSlot.pm : PodcastSlot.am;
}

enum EpisodeStatus { playing, available, upcoming }

class Episode {
  final String id;
  final DateTime date;
  final PodcastSlot slot;

  /// `podcasts.title` — 회차 헤드라인 요약 한 줄. 파이프라인이 채움.
  /// 예: "금리 3.75% 인상, 추경 35조 합의, 美 CPI 둔화"
  final String? title;

  final String? script;

  /// Supabase Storage 오브젝트 키 (예: "2026-04-19/briefing_AM.mp3").
  /// null 이면 아직 오디오 미생성 / 정리됨 상태.
  final String? audioPath;

  /// 회차에 다뤄진 주요 키워드 — `podcasts.covered_keywords`.
  final List<String> coveredKeywords;

  /// duration 컬럼은 DB에 아직 없음. 나중에 추가되면 채워짐.
  final Duration? duration;

  final DateTime createdAt;

  const Episode({
    required this.id,
    required this.date,
    required this.slot,
    this.title,
    this.script,
    this.audioPath,
    this.coveredKeywords = const [],
    this.duration,
    required this.createdAt,
  });

  factory Episode.fromRow(Map<String, dynamic> row) {
    final rawKeywords = row['covered_keywords'];
    final keywords = rawKeywords is List
        ? rawKeywords.whereType<String>().toList()
        : const <String>[];
    final durSec = (row['duration_sec'] as num?)?.toInt();
    return Episode(
      id: row['id'] as String,
      date: DateTime.parse(row['date'] as String),
      slot: PodcastSlotX.fromCode(row['slot'] as String),
      title: row['title'] as String?,
      script: row['script'] as String?,
      audioPath: row['audio_path'] as String?,
      coveredKeywords: keywords,
      duration: durSec != null ? Duration(seconds: durSec) : null,
      createdAt: DateTime.parse(row['created_at'] as String).toLocal(),
    );
  }

  /// 타일용 짧은 라벨: "4. 19."
  String get dateShort => DateFormat('M. d.').format(date);

  /// 긴 라벨: "4월 19일"
  String get dateKo => DateFormat('M월 d일', 'ko').format(date);

  /// 요일 1자: 월/화/수/목/금/토/일
  String get dayShort {
    const labels = ['월', '화', '수', '목', '금', '토', '일'];
    return labels[date.weekday - 1];
  }

  /// 재생 화면 title 영역에 쓰는 fallback.
  String get displayTitle =>
      (title != null && title!.trim().isNotEmpty) ? title!.trim() : '오늘의 브리핑';

  /// 듀레이션을 "mm:ss" 로. 모르면 "—:—".
  String get durationLabel {
    final d = duration;
    if (d == null) return '—:—';
    final m = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final s = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$m:$s';
  }

  Episode copyWith({Duration? duration}) => Episode(
        id: id,
        date: date,
        slot: slot,
        title: title,
        script: script,
        audioPath: audioPath,
        coveredKeywords: coveredKeywords,
        duration: duration ?? this.duration,
        createdAt: createdAt,
      );
}
