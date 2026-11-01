import React, { createContext, useContext, useEffect, useState } from "react";
import { api, User } from "../api/client";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  signup: (data: { email: string; username: string; password: string; full_name?: string }) => Promise<void>;
  login: (dataOrIdentifier: string | { username_or_email: string; password?: string }, password?: string) => Promise<void>;
  directLogin: (username: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = async () => {
    const token = api.getToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const u = await api.getMe();
      setUser(u);
      setError(null);
    } catch (err: any) {
      console.warn("Session expired or invalid:", err.message);
      api.setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const signup = async (data: { email: string; username: string; password: string; full_name?: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.signup(data);
      setUser(res.user);
    } catch (err: any) {
      setError(err.message || "Failed to create account");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (
    dataOrIdentifier: string | { username_or_email: string; password?: string },
    password?: string
  ) => {
    setIsLoading(true);
    setError(null);
    try {
      if (typeof dataOrIdentifier === "object") {
        if (dataOrIdentifier.password) {
          const res = await api.login({
            username_or_email: dataOrIdentifier.username_or_email,
            password: dataOrIdentifier.password,
          });
          setUser(res.user);
        } else {
          const res = await api.directLogin(dataOrIdentifier.username_or_email);
          setUser(res.user);
        }
      } else if (password) {
        const res = await api.login({ username_or_email: dataOrIdentifier, password });
        setUser(res.user);
      } else {
        const res = await api.directLogin(dataOrIdentifier);
        setUser(res.user);
      }
    } catch (err: any) {
      setError(err.message || "Failed to sign in");
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const directLogin = async (username: string) => {
    return login(username);
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await api.logout();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        error,
        signup,
        login,
        directLogin,
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
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
