import { Audio, AVPlaybackStatus } from "expo-av";
import { FrequencyItem } from "../types/api";

class AudioPlayerService {
  private sound: Audio.Sound | null = null;
  private currentTrack: FrequencyItem | null = null;
  private isPlaying: boolean = false;
  private position: number = 0;
  private duration: number = 0;
  private listeners: Set<(state: AudioPlayerState) => void> = new Set();

  constructor() {
    this.setupAudio();
  }

  private async setupAudio() {
    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        staysActiveInBackground: true,
        playsInSilentModeIOS: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false,
      });
    } catch (error) {
      console.error("Failed to setup audio:", error);
    }
  }

  private notifyListeners() {
    const state = this.getState();
    this.listeners.forEach((listener) => listener(state));
  }

  subscribe(listener: (state: AudioPlayerState) => void) {
    this.listeners.add(listener);
    // 즉시 현재 상태 전달
    listener(this.getState());
    return () => {
      this.listeners.delete(listener);
    };
  }

  private onPlaybackStatusUpdate = (status: AVPlaybackStatus) => {
    if (status.isLoaded) {
      this.isPlaying = status.isPlaying;
      this.position = status.positionMillis;
      this.duration = status.durationMillis || 0;

      if (status.didJustFinish) {
        this.handleTrackEnd();
      }

      this.notifyListeners();
    }
  };

  async loadTrack(track: FrequencyItem) {
    try {
      // 기존 사운드 정리
      if (this.sound) {
        await this.sound.unloadAsync();
      }

      this.currentTrack = track;

      const { sound } = await Audio.Sound.createAsync(
        { uri: track.audio_url },
        { shouldPlay: false },
        this.onPlaybackStatusUpdate
      );

      this.sound = sound;
      this.notifyListeners();
    } catch (error) {
      console.error("Failed to load track:", error);
      throw error;
    }
  }

  async play() {
    if (!this.sound) return;

    try {
      await this.sound.playAsync();
      this.isPlaying = true;
      this.notifyListeners();
    } catch (error) {
      console.error("Failed to play:", error);
    }
  }

  async pause() {
    if (!this.sound) return;

    try {
      await this.sound.pauseAsync();
      this.isPlaying = false;
      this.notifyListeners();
    } catch (error) {
      console.error("Failed to pause:", error);
    }
  }

  async togglePlayPause() {
    if (this.isPlaying) {
      await this.pause();
    } else {
      await this.play();
    }
  }

  async seekTo(positionMillis: number) {
    if (!this.sound) return;

    try {
      await this.sound.setPositionAsync(positionMillis);
      this.position = positionMillis;
      this.notifyListeners();
    } catch (error) {
      console.error("Failed to seek:", error);
    }
  }

  async skip(seconds: number) {
    const newPosition = Math.max(0, Math.min(this.position + seconds * 1000, this.duration));
    await this.seekTo(newPosition);
  }

  async setPlaybackRate(rate: number) {
    if (!this.sound) return;

    try {
      await this.sound.setRateAsync(rate, true);
      this.notifyListeners();
    } catch (error) {
      console.error("Failed to set playback rate:", error);
    }
  }

  private handleTrackEnd() {
    this.isPlaying = false;
    this.notifyListeners();
  }

  async stop() {
    if (!this.sound) return;

    try {
      await this.sound.stopAsync();
      await this.sound.unloadAsync();
      this.sound = null;
      this.currentTrack = null;
      this.isPlaying = false;
      this.position = 0;
      this.duration = 0;
      this.notifyListeners();
    } catch (error) {
      console.error("Failed to stop:", error);
    }
  }

  getState(): AudioPlayerState {
    return {
      currentTrack: this.currentTrack,
      isPlaying: this.isPlaying,
      position: this.position,
      duration: this.duration,
      progress: this.duration > 0 ? this.position / this.duration : 0,
    };
  }

  async cleanup() {
    if (this.sound) {
      await this.sound.unloadAsync();
    }
    this.listeners.clear();
  }
}

export interface AudioPlayerState {
  currentTrack: FrequencyItem | null;
  isPlaying: boolean;
  position: number;
  duration: number;
  progress: number;
}

export const audioPlayer = new AudioPlayerService();
