import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authService } from "@/services/auth.service";
import type { AuthState, LoginCredentials, User } from "@/types";
import { tokenStorage } from "@/utils/tokenStorage";

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const accessToken = tokenStorage.getAccessToken();
    if (!accessToken) {
      setUser(null);
      return;
    }

    const currentUser = await authService.getCurrentUser();
    setUser(currentUser);
  }, []);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        await refreshUser();
      } catch {
        tokenStorage.clearTokens();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    void bootstrap();
  }, [refreshUser]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const tokens = await authService.login(credentials);
    tokenStorage.setTokens(tokens.access, tokens.refresh);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    tokenStorage.clearTokens();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      logout,
      refreshUser,
    }),
    [user, isLoading, login, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
