import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { todayKst } from '@/lib/date';
import type { NewsCard } from '@/types/db';
import { CATEGORIES, type CategoryId } from '@/theme/categories';

type HomeTab = 'all' | 'my' | CategoryId;

/**
 * Fetch news cards for the Home tab.
 *   'all'  — top-1 of each category (by rank)
 *   'my'   — top-ranked across user's interest categories
 *   <cat>  — up to 20 cards for that category, sorted by rank
 */
export function useNewsCards(
  tab: HomeTab,
  interests: CategoryId[] = [],
  date: string = todayKst()
) {
  const [cards, setCards] = useState<NewsCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        if (tab === 'all') {
          // Top-1 per category. Fetch rank=1 for every known category.
          const cats = CATEGORIES.map((c) => c.id);
          const { data, error: qErr } = await supabase
            .from('news_cards')
            .select('*')
            .eq('date', date)
            .eq('rank', 1)
            .in('category', cats);
          if (qErr) throw qErr;
          if (!cancelled) setCards(((data as NewsCard[]) ?? []).sort((a, b) => a.category.localeCompare(b.category)));
        } else if (tab === 'my') {
          if (interests.length === 0) {
            if (!cancelled) setCards([]);
          } else {
            const { data, error: qErr } = await supabase
              .from('news_cards')
              .select('*')
              .eq('date', date)
              .in('category', interests)
              .lte('rank', 5)
              .order('rank', { ascending: true });
            if (qErr) throw qErr;
            if (!cancelled) setCards((data as NewsCard[]) ?? []);
          }
        } else {
          const { data, error: qErr } = await supabase
            .from('news_cards')
            .select('*')
            .eq('date', date)
            .eq('category', tab)
            .order('rank', { ascending: true })
            .limit(20);
          if (qErr) throw qErr;
          if (!cancelled) setCards((data as NewsCard[]) ?? []);
        }
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [tab, interests.join(','), date]);

  return { cards, loading, error };
}

export function useNewsCard(newsId: string | undefined | null) {
  const [card, setCard] = useState<NewsCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!newsId) {
      setCard(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const { data, error: qErr } = await supabase
          .from('news_cards')
          .select('*')
          .eq('news_id', newsId)
          .maybeSingle();
        if (qErr) throw qErr;
        if (!cancelled) setCard((data as NewsCard) ?? null);
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [newsId]);

  return { card, loading, error };
}
