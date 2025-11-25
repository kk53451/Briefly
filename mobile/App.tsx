/**
 * Briefly Mobile App - Main Entry Point
 * AI-powered news podcast platform
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { ThemeProvider } from './src/contexts/ThemeContext';
import { AuthProvider } from './src/contexts/AuthContext';
import { AudioPlayerProvider } from './src/contexts/AudioPlayerContext';
import { RootNavigator } from './src/navigation/RootNavigator';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AudioPlayerProvider>
          <RootNavigator />
          <StatusBar style="auto" />
        </AudioPlayerProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
