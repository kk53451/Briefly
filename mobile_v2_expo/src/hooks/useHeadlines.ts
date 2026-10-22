import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { todayKst } from '@/lib/date';
import type { HeadlineItem, HeadlineRow, Slot } from '@/types/db';

export interface TodayHeadline extends HeadlineItem {
  category: string;  // api_name (e.g. "economy")
}

/**
 * Aggregate today's headlines across all categories for a given slot.
 * Returns ranked topic cards (one per headline row's top-ranked item, flattened & sorted by cluster_size desc).
 */
export function useHeadlines(slot: Slot, date: string = todayKst()) {
  const [items, setItems] = useState<TodayHeadline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const { data, error: qErr } = await supabase
          .from('headlines')
          .select('category, items')
          .eq('date', date)
          .eq('slot', slot);

        if (qErr) throw qErr;

        const rows = (data ?? []) as Pick<HeadlineRow, 'category' | 'items'>[];
        const flat: TodayHeadline[] = [];
        for (const row of rows) {
          for (const item of row.items ?? []) {
            flat.push({ ...item, category: row.category });
          }
        }

        // 가장 큰 클러스터 먼저. topic_id로 동률 해소.
        flat.sort((a, b) =>
          b.cluster_size - a.cluster_size || a.topic_id - b.topic_id
        );

        if (!cancelled) setItems(flat.slice(0, 6));
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [slot, date]);

  return { items, loading, error };
}
