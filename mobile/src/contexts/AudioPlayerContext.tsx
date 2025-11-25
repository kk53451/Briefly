/**
 * Audio Player Context for managing podcast playback
 * Supports background audio with Expo AV
 */

import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo } from 'react';
import { Audio, AVPlaybackStatus } from 'expo-av';
import { FrequencyItem } from '../types/api';

interface AudioPlayerContextType {
  currentTrack: FrequencyItem | null;
  isPlaying: boolean;
  isLoading: boolean;
  position: number;
  duration: number;
  playbackRate: number;
  isRepeating: boolean;
  play: (track: FrequencyItem) => Promise<void>;
  pause: () => Promise<void>;
  resume: () => Promise<void>;
  stop: () => Promise<void>;
  seekTo: (position: number) => Promise<void>;
  skipForward: (seconds: number) => Promise<void>;
  skipBackward: (seconds: number) => Promise<void>;
  setPlaybackRate: (rate: number) => Promise<void>;
  toggleRepeat: () => void;
}

const AudioPlayerContext = createContext<AudioPlayerContextType | undefined>(undefined);

export const AudioPlayerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [currentTrack, setCurrentTrack] = useState<FrequencyItem | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRateState] = useState(1.0);
  const [isRepeating, setIsRepeating] = useState(false);

  useEffect(() => {
    setupAudio();
    return () => {
      cleanupSound();
    };
  }, []);

  const setupAudio = async () => {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        staysActiveInBackground: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
    } catch (error) {
      console.error('Failed to setup audio:', error);
    }
  };

  const cleanupSound = async () => {
    if (sound) {
      try {
        await sound.unloadAsync();
      } catch (error) {
        console.error('Failed to cleanup sound:', error);
      }
    }
  };

  const onPlaybackStatusUpdate = (status: AVPlaybackStatus) => {
    if (status.isLoaded) {
      setPosition(status.positionMillis);
      setDuration(status.durationMillis || 0);
      setIsPlaying(status.isPlaying);
      setIsLoading(false);

      // Handle track end
      if (status.didJustFinish && !status.isLooping) {
        if (isRepeating) {
          // Restart from beginning
          sound?.replayAsync();
        } else {
          setIsPlaying(false);
          setPosition(0);
        }
      }
    }
  };

  const play = async (track: FrequencyItem) => {
    try {
      setIsLoading(true);

      // Stop and unload current sound
      if (sound) {
        await sound.unloadAsync();
      }

      // Load and play new track
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: track.audio_url },
        { shouldPlay: true, rate: playbackRate },
        onPlaybackStatusUpdate
      );

      setSound(newSound);
      setCurrentTrack(track);
      setIsPlaying(true);
    } catch (error) {
      console.error('Failed to play audio:', error);
      setIsLoading(false);
      throw error;
    }
  };

  const pause = async () => {
    try {
      if (sound) {
        await sound.pauseAsync();
        setIsPlaying(false);
      }
    } catch (error) {
      console.error('Failed to pause:', error);
    }
  };

  const resume = async () => {
    try {
      if (sound) {
        await sound.playAsync();
        setIsPlaying(true);
      }
    } catch (error) {
      console.error('Failed to resume:', error);
    }
  };

  const stop = async () => {
    try {
      if (sound) {
        await sound.stopAsync();
        await sound.unloadAsync();
        setSound(null);
        setCurrentTrack(null);
        setIsPlaying(false);
        setPosition(0);
        setDuration(0);
      }
    } catch (error) {
      console.error('Failed to stop:', error);
    }
  };

  const seekTo = async (positionMillis: number) => {
    try {
      if (sound) {
        await sound.setPositionAsync(positionMillis);
      }
    } catch (error) {
      console.error('Failed to seek:', error);
    }
  };

  const skipForward = async (seconds: number) => {
    const newPosition = Math.min(position + seconds * 1000, duration);
    await seekTo(newPosition);
  };

  const skipBackward = async (seconds: number) => {
    const newPosition = Math.max(position - seconds * 1000, 0);
    await seekTo(newPosition);
  };

  const setPlaybackRate = async (rate: number) => {
    try {
      if (sound) {
        await sound.setRateAsync(rate, true);
        setPlaybackRateState(rate);
      }
    } catch (error) {
      console.error('Failed to set playback rate:', error);
    }
  };

  const toggleRepeat = () => {
    setIsRepeating(!isRepeating);
  };

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo(
    () => ({
      currentTrack,
      isPlaying,
      isLoading,
      position,
      duration,
      playbackRate,
      isRepeating,
      play,
      pause,
      resume,
      stop,
      seekTo,
      skipForward,
      skipBackward,
      setPlaybackRate,
      toggleRepeat,
    }),
    [
      currentTrack,
      isPlaying,
      isLoading,
      position,
      duration,
      playbackRate,
      isRepeating,
    ]
  );

  return (
    <AudioPlayerContext.Provider value={contextValue}>
      {children}
    </AudioPlayerContext.Provider>
  );
};

export const useAudioPlayer = (): AudioPlayerContextType => {
  const context = useContext(AudioPlayerContext);
  if (!context) {
    throw new Error('useAudioPlayer must be used within AudioPlayerProvider');
  }
  return context;
};
