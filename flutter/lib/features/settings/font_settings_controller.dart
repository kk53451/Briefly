import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 폰트 설정 — 디자인 패키지 font-settings.jsx 의 SERIF / SANS / SIZE 옵션을
/// 그대로 보존. 현재 번들된 폰트는 NotoSerifKR + Pretendard 뿐이라 그 외 폰트는
/// `available: false` 로 잠겨 있고, 화면에서 "준비 중" 배지로 표시됨.

enum FontSizeStep {
  sm(id: 'sm', label: '작게', mult: 0.92),
  md(id: 'md', label: '보통', mult: 1.00),
  lg(id: 'lg', label: '크게', mult: 1.12),
  xl(id: 'xl', label: '아주 크게', mult: 1.24);

  final String id;
  final String label;
  final double mult;
  const FontSizeStep({required this.id, required this.label, required this.mult});

  static FontSizeStep fromId(String? id) =>
      values.firstWhere((e) => e.id == id, orElse: () => md);
}

class FontOption {
  final String id;
  final String name;
  /// Flutter 가 인식하는 family. 미번들 폰트는 sentinel 만 들고 있고
  /// `available=false` 라 실제로는 사용되지 않음.
  final String family;
  final int weight;
  final bool available;
  const FontOption({
    required this.id,
    required this.name,
    required this.family,
    required this.weight,
    this.available = true,
  });
}

const kSerifOptions = <FontOption>[
  FontOption(id: 'noto-serif',     name: 'Noto Serif KR',       family: 'NotoSerifKR', weight: 700),
  FontOption(id: 'noto-serif-bold',name: 'Noto Serif KR Black', family: 'NotoSerifKR', weight: 900),
  FontOption(id: 'nanum-myeongjo', name: 'Nanum Myeongjo',      family: 'NotoSerifKR', weight: 700, available: false),
  FontOption(id: 'gowun-batang',   name: 'Gowun Batang',        family: 'NotoSerifKR', weight: 700, available: false),
];

const kSansOptions = <FontOption>[
  FontOption(id: 'pretendard',    name: 'Pretendard',        family: 'Pretendard', weight: 500),
  FontOption(id: 'noto-sans',     name: 'Noto Sans KR',      family: 'Pretendard', weight: 500, available: false),
  FontOption(id: 'ibm-plex-sans', name: 'IBM Plex Sans KR',  family: 'Pretendard', weight: 500, available: false),
  FontOption(id: 'gowun-dodum',   name: 'Gowun Dodum',       family: 'Pretendard', weight: 400, available: false),
];

FontOption serifById(String id) =>
    kSerifOptions.firstWhere((o) => o.id == id, orElse: () => kSerifOptions.first);
FontOption sansById(String id) =>
    kSansOptions.firstWhere((o) => o.id == id, orElse: () => kSansOptions.first);

@immutable
class FontSettings {
  final String serifId;
  final String sansId;
  final FontSizeStep size;
  const FontSettings({
    required this.serifId,
    required this.sansId,
    required this.size,
  });

  static const initial = FontSettings(
    serifId: 'noto-serif',
    sansId: 'pretendard',
    size: FontSizeStep.md,
  );

  FontSettings copyWith({String? serifId, String? sansId, FontSizeStep? size}) =>
      FontSettings(
        serifId: serifId ?? this.serifId,
        sansId: sansId ?? this.sansId,
        size: size ?? this.size,
      );

  @override
  bool operator ==(Object other) =>
      other is FontSettings &&
      other.serifId == serifId &&
      other.sansId == sansId &&
      other.size == size;

  @override
  int get hashCode => Object.hash(serifId, sansId, size);
}

class FontSettingsNotifier extends StateNotifier<FontSettings> {
  FontSettingsNotifier() : super(FontSettings.initial) {
    _load();
  }

  static const _kSerif = 'font_settings_serif';
  static const _kSans  = 'font_settings_sans';
  static const _kSize  = 'font_settings_size';

  Future<void> _load() async {
    try {
      final p = await SharedPreferences.getInstance();
      state = FontSettings(
        serifId: p.getString(_kSerif) ?? FontSettings.initial.serifId,
        sansId:  p.getString(_kSans)  ?? FontSettings.initial.sansId,
        size:    FontSizeStep.fromId(p.getString(_kSize)),
      );
    } catch (e) {
      if (kDebugMode) debugPrint('FontSettings load failed: $e');
    }
  }

  Future<void> apply(FontSettings next) async {
    state = next;
    try {
      final p = await SharedPreferences.getInstance();
      await p.setString(_kSerif, next.serifId);
      await p.setString(_kSans,  next.sansId);
      await p.setString(_kSize,  next.size.id);
    } catch (e) {
      if (kDebugMode) debugPrint('FontSettings save failed: $e');
    }
  }
}

final fontSettingsProvider =
    StateNotifierProvider<FontSettingsNotifier, FontSettings>(
        (_) => FontSettingsNotifier());
