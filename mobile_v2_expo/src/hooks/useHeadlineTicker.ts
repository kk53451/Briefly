import { useEffect, useState } from 'react';

type Phase = 'typing' | 'holding' | 'erasing' | 'gap';

interface Options {
  typeSpeed?: number;
  eraseSpeed?: number;
  holdMs?: number;
  gapMs?: number;
}

/** Typewriter cycle: types → holds → erases → next. Mirrors briefly_design/login.jsx. */
export function useHeadlineTicker(
  headlines: string[],
  { typeSpeed = 70, eraseSpeed = 28, holdMs = 1400, gapMs = 400 }: Options = {}
) {
  const [idx, setIdx] = useState(0);
  const [text, setText] = useState('');
  const [phase, setPhase] = useState<Phase>('typing');

  useEffect(() => {
    const current = headlines[idx % headlines.length] ?? '';
    let timer: ReturnType<typeof setTimeout>;

    if (phase === 'typing') {
      if (text.length < current.length) {
        timer = setTimeout(() => setText(current.slice(0, text.length + 1)), typeSpeed);
      } else {
        timer = setTimeout(() => setPhase('holding'), 0);
      }
    } else if (phase === 'holding') {
      timer = setTimeout(() => setPhase('erasing'), holdMs);
    } else if (phase === 'erasing') {
      if (text.length > 0) {
        timer = setTimeout(() => setText(current.slice(0, text.length - 1)), eraseSpeed);
      } else {
        timer = setTimeout(() => setPhase('gap'), 0);
      }
    } else {
      timer = setTimeout(() => {
        setIdx((i) => i + 1);
        setPhase('typing');
      }, gapMs);
    }

    return () => clearTimeout(timer);
  }, [text, phase, idx, headlines, typeSpeed, eraseSpeed, holdMs, gapMs]);

  return text;
}
