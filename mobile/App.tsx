import React from "react";
import { StatusBar } from "expo-status-bar";
import { AuthProvider } from "./src/contexts/AuthContext";
import { AudioPlayerProvider } from "./src/contexts/AudioPlayerContext";
import RootNavigator from "./src/navigation/RootNavigator";

export default function App() {
  return (
    <AuthProvider>
      <AudioPlayerProvider>
        <StatusBar style="light" backgroundColor="#0f172a" />
        <RootNavigator />
      </AudioPlayerProvider>
    </AuthProvider>
  );
}
