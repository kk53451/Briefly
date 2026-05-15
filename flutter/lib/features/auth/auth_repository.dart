import 'package:google_sign_in/google_sign_in.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../core/config/env.dart';
import '../../core/config/supabase.dart';

class AuthRepository {
  const AuthRepository();

  static bool _googleInitialized = false;
  static const List<String> _googleScopes = <String>['email', 'profile'];

  /// Kakao: Supabase web OAuth flow. 브라우저/WebView로 열리며
  /// `briefly://auth-callback` 딥링크로 supabase_flutter 가 세션을 받아옴.
  Future<void> signInWithKakao() async {
    await supabase.auth.signInWithOAuth(
      OAuthProvider.kakao,
      redirectTo: 'briefly://auth-callback',
      authScreenLaunchMode: LaunchMode.externalApplication,
    );
  }

  /// Google: native Sign-In (7.x, Credential Manager) → id_token → Supabase signInWithIdToken.
  /// Google native SDK 는 nonce 를 지원하지 않으므로 전달하지 않음.
  /// (Supabase Auth 의 Google provider 는 이 경우 nonce 검증을 건너뜀.)
  Future<AuthResponse> signInWithGoogle() async {
    await _ensureGoogleInitialized();

    final signIn = GoogleSignIn.instance;
    if (!signIn.supportsAuthenticate()) {
      throw const AuthException('이 플랫폼에서는 Google 네이티브 로그인을 지원하지 않습니다');
    }

    final GoogleSignInAccount googleUser;
    try {
      googleUser = await signIn.authenticate(scopeHint: _googleScopes);
    } on GoogleSignInException catch (e) {
      if (e.code == GoogleSignInExceptionCode.canceled) {
        throw const AuthException('Google 로그인 취소됨');
      }
      rethrow;
    }

    final idToken = googleUser.authentication.idToken;
    if (idToken == null) {
      throw const AuthException('Google id_token 없음');
    }

    // 7.x: 인증(authenticate)과 인가(authorization)가 분리됨.
    // email/profile 은 authenticate 단계에서 승인되어 추가 UI 없이 토큰 조회 가능.
    final authz =
        await googleUser.authorizationClient.authorizationForScopes(_googleScopes) ??
            await googleUser.authorizationClient.authorizeScopes(_googleScopes);

    return supabase.auth.signInWithIdToken(
      provider: OAuthProvider.google,
      idToken: idToken,
      accessToken: authz.accessToken,
    );
  }

  Future<void> signOut() => supabase.auth.signOut();

  Future<void> _ensureGoogleInitialized() async {
    if (_googleInitialized) return;
    await GoogleSignIn.instance.initialize(
      clientId: Env.googleIosClientId,
      serverClientId: Env.googleWebClientId,
    );
    _googleInitialized = true;
  }
}
