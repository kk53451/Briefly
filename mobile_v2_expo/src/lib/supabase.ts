import 'react-native-url-polyfill/auto';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  // Fail loudly at dev time. `.env` must be populated for the app to function.
  console.warn(
    '[supabase] Missing EXPO_PUBLIC_SUPABASE_URL or EXPO_PUBLIC_SUPABASE_ANON_KEY. See .env.example.'
  );
}

export const supabase = createClient(
  SUPABASE_URL ?? 'http://invalid.local',
  SUPABASE_ANON_KEY ?? 'invalid',
  {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  }
);

export const AUDIO_BUCKET =
  process.env.EXPO_PUBLIC_SUPABASE_AUDIO_BUCKET ?? 'briefly-audio';

/** Build a public URL for an audio object stored at `audio_path`. */
export function audioPublicUrl(audioPath: string | null | undefined): string | null {
  if (!audioPath) return null;
  const { data } = supabase.storage.from(AUDIO_BUCKET).getPublicUrl(audioPath);
  return data.publicUrl;
}
