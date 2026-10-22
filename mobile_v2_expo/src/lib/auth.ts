import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { supabase } from './supabase';

WebBrowser.maybeCompleteAuthSession();

export type OAuthProvider = 'kakao' | 'google';

/**
 * Drive a Supabase OAuth round-trip through an in-app browser and install the
 * returned tokens on the client. Returns `true` when the session was set.
 */
export async function signInWithProvider(provider: OAuthProvider): Promise<boolean> {
  const redirectTo = Linking.createURL('/auth-callback');

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: { redirectTo, skipBrowserRedirect: true },
  });
  if (error) throw error;
  if (!data?.url) throw new Error('OAuth URL missing');

  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
  if (result.type !== 'success' || !result.url) return false;

  const url = new URL(result.url);
  const params = new URLSearchParams(
    url.hash.startsWith('#') ? url.hash.slice(1) : url.search
  );
  const access_token = params.get('access_token');
  const refresh_token = params.get('refresh_token');
  if (!access_token || !refresh_token) return false;

  await supabase.auth.setSession({ access_token, refresh_token });
  return true;
}
