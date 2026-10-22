import { useCallback, useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import type { Profile } from '@/types/db';

export function useProfile(userId: string | null | undefined) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    if (!userId) {
      setProfile(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const { data, error: qErr } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .maybeSingle();
      if (qErr) throw qErr;
      setProfile((data as Profile) ?? null);
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => { load(); }, [load]);

  const update = useCallback(async (patch: Partial<Profile>) => {
    if (!userId) throw new Error('Not authenticated');
    const { data, error: qErr } = await supabase
      .from('profiles')
      .update(patch)
      .eq('id', userId)
      .select()
      .single();
    if (qErr) throw qErr;
    setProfile(data as Profile);
    return data as Profile;
  }, [userId]);

  return { profile, loading, error, reload: load, update };
}
