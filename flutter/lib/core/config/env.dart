import 'package:flutter_dotenv/flutter_dotenv.dart';

class Env {
  static String get supabaseUrl => _require('SUPABASE_URL');
  static String get supabaseAnonKey => _require('SUPABASE_ANON_KEY');
  static String get audioBucket =>
      dotenv.env['SUPABASE_AUDIO_BUCKET'] ?? 'briefly-audio';

  /// Google Web Client ID. Google Cloud Console → OAuth 2.0 Web client.
  /// Supabase Auth → Google provider 에 입력한 값과 동일해야 함.
  static String get googleWebClientId => _require('GOOGLE_WEB_CLIENT_ID');

  /// Google iOS Client ID. iOS 빌드에서만 필요. Android 전용 개발 중엔 비워도 OK.
  /// 빈 문자열 / placeholder(`<...>`) 모두 null 처리.
  static String? get googleIosClientId {
    final v = dotenv.env['GOOGLE_IOS_CLIENT_ID'];
    if (v == null || v.trim().isEmpty || v.contains('<')) return null;
    return v;
  }

  static String _require(String key) {
    final value = dotenv.env[key];
    if (value == null || value.isEmpty) {
      throw StateError('$key is not set in .env');
    }
    // placeholder 검사: `<...>` 를 포함하면 명시적 에러 (예: `<google-web-client-id>.apps.googleusercontent.com`).
    if (value.contains('<') || value.contains('>')) {
      throw StateError('$key 가 placeholder 값입니다 ($value). .env 에 실제 값을 넣으세요.');
    }
    return value;
  }
}
