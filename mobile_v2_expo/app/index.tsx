import { useEffect } from 'react';
import { Redirect } from 'expo-router';
import { ActivityIndicator, View } from 'react-native';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';
import { colors } from '@/theme/tokens';

/**
 * Entry gate — decides between (auth) and (tabs) based on session + onboarding state.
 */
export default function Index() {
  const { session, loading: authLoading } = useAuth();
  const { profile, loading: profileLoading } = useProfile(session?.user?.id ?? null);

  useEffect(() => { /* keep hook shape stable */ }, [session]);

  if (authLoading || (session && profileLoading)) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.paper, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.ink} />
      </View>
    );
  }

  if (!session) return <Redirect href="/(auth)/login" />;
  if (profile && !profile.onboarding_completed) return <Redirect href="/(auth)/onboarding" />;
  return <Redirect href="/(tabs)/today" />;
}
