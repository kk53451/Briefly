import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { audioPlayer, AudioPlayerState } from "../services/audioPlayer";
import { FrequencyItem } from "../types/api";

interface AudioPlayerContextType extends AudioPlayerState {
  loadTrack: (track: FrequencyItem) => Promise<void>;
  play: () => Promise<void>;
  pause: () => Promise<void>;
  togglePlayPause: () => Promise<void>;
  seekTo: (positionMillis: number) => Promise<void>;
  skip: (seconds: number) => Promise<void>;
  setPlaybackRate: (rate: number) => Promise<void>;
  stop: () => Promise<void>;
}

const AudioPlayerContext = createContext<AudioPlayerContextType | undefined>(undefined);

export const AudioPlayerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AudioPlayerState>(audioPlayer.getState());

  useEffect(() => {
    const unsubscribe = audioPlayer.subscribe((newState) => {
      setState(newState);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const value: AudioPlayerContextType = {
    ...state,
    loadTrack: audioPlayer.loadTrack.bind(audioPlayer),
    play: audioPlayer.play.bind(audioPlayer),
    pause: audioPlayer.pause.bind(audioPlayer),
    togglePlayPause: audioPlayer.togglePlayPause.bind(audioPlayer),
    seekTo: audioPlayer.seekTo.bind(audioPlayer),
    skip: audioPlayer.skip.bind(audioPlayer),
    setPlaybackRate: audioPlayer.setPlaybackRate.bind(audioPlayer),
    stop: audioPlayer.stop.bind(audioPlayer),
  };

  return <AudioPlayerContext.Provider value={value}>{children}</AudioPlayerContext.Provider>;
};

export const useAudioPlayer = (): AudioPlayerContextType => {
  const context = useContext(AudioPlayerContext);
  if (!context) {
    throw new Error("useAudioPlayer must be used within AudioPlayerProvider");
  }
  return context;
};
