import { useCallback, useEffect, useRef, useState } from 'react';
import { Audio, AVPlaybackStatus } from 'expo-av';

interface State {
  isLoaded: boolean;
  isPlaying: boolean;
  positionMillis: number;
  durationMillis: number;
  rate: number;
  loading: boolean;
  error: string | null;
}

const INITIAL: State = {
  isLoaded: false,
  isPlaying: false,
  positionMillis: 0,
  durationMillis: 0,
  rate: 1,
  loading: false,
  error: null,
};

export function usePodcastPlayer(audioUrl: string | null) {
  const soundRef = useRef<Audio.Sound | null>(null);
  const [state, setState] = useState<State>(INITIAL);

  const onStatus = useCallback((s: AVPlaybackStatus) => {
    if (!s.isLoaded) {
      setState((prev) => ({ ...prev, isLoaded: false, isPlaying: false }));
      return;
    }
    setState((prev) => ({
      ...prev,
      isLoaded: true,
      isPlaying: s.isPlaying,
      positionMillis: s.positionMillis ?? 0,
      durationMillis: s.durationMillis ?? 0,
      rate: s.rate ?? prev.rate,
      loading: false,
    }));
  }, []);

  // Load / swap sound when url changes
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (soundRef.current) {
        await soundRef.current.unloadAsync().catch(() => {});
        soundRef.current = null;
      }
      setState({ ...INITIAL, loading: Boolean(audioUrl) });
      if (!audioUrl) return;
      try {
        await Audio.setAudioModeAsync({
          playsInSilentModeIOS: true,
          staysActiveInBackground: true,
          shouldDuckAndroid: true,
        });
        const { sound } = await Audio.Sound.createAsync(
          { uri: audioUrl },
          { shouldPlay: false },
          onStatus
        );
        if (cancelled) {
          await sound.unloadAsync().catch(() => {});
          return;
        }
        soundRef.current = sound;
      } catch (e) {
        if (!cancelled) {
          setState({ ...INITIAL, error: (e as Error).message });
        }
      }
    };
    load();
    return () => {
      cancelled = true;
      soundRef.current?.unloadAsync().catch(() => {});
      soundRef.current = null;
    };
  }, [audioUrl, onStatus]);

  const toggle = useCallback(async () => {
    const s = soundRef.current;
    if (!s) return;
    const status = await s.getStatusAsync();
    if (!status.isLoaded) return;
    if (status.isPlaying) await s.pauseAsync();
    else await s.playAsync();
  }, []);

  const seekBy = useCallback(async (deltaMs: number) => {
    const s = soundRef.current;
    if (!s) return;
    const status = await s.getStatusAsync();
    if (!status.isLoaded) return;
    const next = Math.max(0, Math.min(status.durationMillis ?? 0, (status.positionMillis ?? 0) + deltaMs));
    await s.setPositionAsync(next);
  }, []);

  const seekTo = useCallback(async (millis: number) => {
    const s = soundRef.current;
    if (!s) return;
    await s.setPositionAsync(millis);
  }, []);

  const setRate = useCallback(async (rate: number) => {
    const s = soundRef.current;
    if (!s) return;
    await s.setRateAsync(rate, true);
    setState((prev) => ({ ...prev, rate }));
  }, []);

  return { ...state, toggle, seekBy, seekTo, setRate };
}

export function formatMs(ms: number): string {
  if (!ms || !isFinite(ms)) return '00:00';
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
