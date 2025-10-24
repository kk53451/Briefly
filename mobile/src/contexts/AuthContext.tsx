import React, { createContext, useState, useContext, useEffect, ReactNode } from "react";
import { apiClient } from "../services/api";
import { storage } from "../services/storage";
import type { UserProfile } from "../types/api";

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await storage.getAccessToken();
      if (token) {
        const userProfile = await apiClient.getCurrentUser();
        setUser(userProfile);
      }
    } catch (error) {
      console.error("Auth check failed:", error);
      await storage.clear();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (token: string) => {
    await storage.setAccessToken(token);
    const userProfile = await apiClient.getCurrentUser();
    setUser(userProfile);
    await storage.setUserProfile(userProfile);
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      await storage.clear();
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const userProfile = await apiClient.getCurrentUser();
      setUser(userProfile);
      await storage.setUserProfile(userProfile);
    } catch (error) {
      console.error("Failed to refresh user:", error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
