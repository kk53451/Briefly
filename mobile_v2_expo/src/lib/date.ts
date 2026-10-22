/**
 * KST date helpers — the pipeline writes rows keyed by KST date.
 */

const KST_OFFSET_MIN = 9 * 60;

function nowKst(): Date {
  const now = new Date();
  const utcMs = now.getTime() + now.getTimezoneOffset() * 60_000;
  return new Date(utcMs + KST_OFFSET_MIN * 60_000);
}

export function todayKst(): string {
  const d = nowKst();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** AM before 12:00 KST, PM otherwise. */
export function currentSlot(): 'AM' | 'PM' {
  return nowKst().getHours() < 12 ? 'AM' : 'PM';
}

const WEEKDAY_KO = ['일', '월', '화', '수', '목', '금', '토'];

export function formatTodayKorean(date = nowKst()): string {
  return `${date.getMonth() + 1}월 ${date.getDate()}일 ${WEEKDAY_KO[date.getDay()]}요일`;
}

export function formatPublishedAt(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

export function formatDotDate(date: string): string {
  // "2026-04-18" → "2026. 4. 18."
  const [y, m, d] = date.split('-').map(Number);
  return `${y}. ${m}. ${d}.`;
}

export function formatShortDate(date: string): string {
  // "2026-04-18" → "4. 18."
  const [, m, d] = date.split('-').map(Number);
  return `${m}. ${d}.`;
}

export function formatDateKo(date: string): string {
  // "2026-04-18" → "4월 18일"
  const [, m, d] = date.split('-').map(Number);
  return `${m}월 ${d}일`;
}

export function weekdayKo(date: string): string {
  const [y, m, d] = date.split('-').map(Number);
  const wd = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  return ['일', '월', '화', '수', '목', '금', '토'][wd];
}
