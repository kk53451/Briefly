import { useEffect, useMemo, useState } from 'react';
import { supabase, audioPublicUrl } from '@/lib/supabase';
import { currentSlot, todayKst } from '@/lib/date';
import type { PodcastRow, Slot } from '@/types/db';

export interface Episode extends PodcastRow {
  audioUrl: string | null;
}

export type EpisodeStatus = 'playing' | 'available' | 'upcoming' | 'missed';

export interface EpisodeSlot {
  date: string;
  slot: Slot;
  status: EpisodeStatus;
  episode: Episode | null;
}

/** Coerce supabase row → Episode, defaulting nullable fields. */
function toEpisode(row: Partial<PodcastRow> | null | undefined): Episode | null {
  if (!row || !row.id || !row.date || !row.slot || row.script == null || !row.created_at) {
    return null;
  }
  return {
    id: row.id,
    date: row.date,
    slot: row.slot,
    script: row.script,
    title: row.title ?? null,
    audio_path: row.audio_path ?? null,
    duration_sec: row.duration_sec ?? null,
    covered_keywords: row.covered_keywords ?? [],
    created_at: row.created_at,
    audioUrl: audioPublicUrl(row.audio_path ?? null),
  };
}

/** Single comprehensive episode for (date, slot). */
export function usePodcast(slot: Slot, date: string = todayKst()) {
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const { data, error: qErr } = await supabase
          .from('podcasts')
          .select('*')
          .eq('date', date)
          .eq('slot', slot)
          .order('created_at', { ascending: false })
          .limit(1);
        if (qErr) throw qErr;
        const row = (data?.[0] as PodcastRow | undefined) ?? null;
        if (!cancelled) setEpisode(toEpisode(row));
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [slot, date]);

  return { episode, loading, error };
}

function subDays(date: string, days: number): string {
  const [y, m, d] = date.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() - days);
  return `${dt.getUTCFullYear()}-${String(dt.getUTCMonth() + 1).padStart(2, '0')}-${String(dt.getUTCDate()).padStart(2, '0')}`;
}

/**
 * Recent episode history for the playlist.
 * Builds a slot-by-slot timeline for the last `days` days including today's
 * not-yet-published slot as an "upcoming" entry.
 */
export function useRecentEpisodes(days: number = 7) {
  const today = todayKst();
  const nowSlot = currentSlot();
  const fromDate = useMemo(() => subDays(today, days - 1), [today, days]);

  const [rows, setRows] = useState<PodcastRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const { data, error: qErr } = await supabase
          .from('podcasts')
          .select('*')
          .gte('date', fromDate)
          .lte('date', today)
          .order('date', { ascending: false })
          .order('slot', { ascending: false });
        if (qErr) throw qErr;
        if (!cancelled) setRows((data as PodcastRow[]) ?? []);
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [fromDate, today]);

  const timeline = useMemo<EpisodeSlot[]>(() => {
    // Map (date, slot) → first available row (newest wins via outer sort above).
    const byKey = new Map<string, PodcastRow>();
    for (const r of rows) {
      const key = `${r.date}#${r.slot}`;
      if (!byKey.has(key)) byKey.set(key, r);
    }

    const out: EpisodeSlot[] = [];
    for (let i = 0; i < days; i++) {
      const d = subDays(today, i);
      // PM first, then AM — matches "최근 에피소드" display order.
      for (const s of ['PM', 'AM'] as Slot[]) {
        const row = byKey.get(`${d}#${s}`);
        let status: EpisodeStatus;
        if (row) {
          status = d === today && s === nowSlot ? 'playing' : 'available';
        } else if (d === today) {
          // Any missing today-slot is pending publication.
          status = 'upcoming';
        } else {
          status = 'missed';
        }
        out.push({ date: d, slot: s, status, episode: toEpisode(row ?? null) });
      }
    }
    return out;
  }, [rows, today, days, nowSlot]);

  return { timeline, loading, error };
}
