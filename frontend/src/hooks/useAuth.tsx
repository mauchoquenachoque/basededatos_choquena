import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { getCurrentUser, loginWithGoogle, setStoredToken, clearStoredToken } from '../services/api';
import type { User } from '../types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  loginWithGoogle: (idToken: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const current = await getCurrentUser();
        setUser(current);
      } catch {
        clearStoredToken();
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, []);

  const loginWithGoogleFn = useCallback(async (idToken: string) => {
    const auth = await loginWithGoogle(idToken);
    setStoredToken(auth.access_token);
    setUser(auth.user);
    return auth.user;
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, loginWithGoogle: loginWithGoogleFn, logout }),
    [user, loading, loginWithGoogleFn, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="page-content"><div className="spinner" style={{ margin: '80px auto' }} /></div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
