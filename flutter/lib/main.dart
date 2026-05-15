import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:just_audio_background/just_audio_background.dart';

import 'app.dart';
import 'core/config/supabase.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await dotenv.load(fileName: '.env');

  // 한국어 날짜 포매터 (DateFormat('M월 d일', 'ko')) 초기화
  await initializeDateFormatting('ko');

  // just_audio_background 는 Android/iOS 전용. web/desktop 에선 건너뜀.
  // MainActivity 가 FlutterFragmentActivity 상속이면 init 성공.
  // 그래도 안전을 위해 try/catch — 실패 시 재생은 foreground 한정으로 동작.
  if (!kIsWeb) {
    try {
      await JustAudioBackground.init(
        androidNotificationChannelId: 'app.briefly.audio',
        androidNotificationChannelName: 'Briefly 팟캐스트',
        androidNotificationOngoing: true,
      );
    } catch (e, st) {
      debugPrint('⚠️ JustAudioBackground.init failed: $e');
      debugPrintStack(stackTrace: st);
    }
  }

  await initSupabase();

  runApp(const ProviderScope(child: BrieflyApp()));
}
