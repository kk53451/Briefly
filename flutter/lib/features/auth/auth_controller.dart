import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../core/config/supabase.dart';

/// Streams AuthState changes from Supabase.
final authStateProvider = StreamProvider<AuthState>((ref) {
  return supabase.auth.onAuthStateChange;
});

/// Current session (null if signed out). Rebuilds on auth changes.
final sessionProvider = Provider<Session?>((ref) {
  final asyncState = ref.watch(authStateProvider);
  return asyncState.maybeWhen(
    data: (s) => s.session,
    orElse: () => supabase.auth.currentSession,
  );
});
