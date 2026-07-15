import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  login as apiLogin,
  logout as apiLogout,
  refreshToken,
  setAccessToken,
} from "../services/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On mount, try to restore the session via the httpOnly refresh cookie.
  const restore = useCallback(async () => {
    try {
      const data = await refreshToken();
      setAccessToken(data.access_token);
      setUser(data.user);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restore();
  }, [restore]);

  useEffect(() => {
    if (!user) return;

    // Refresh token in background every 10 minutes
    const interval = setInterval(
      async () => {
        try {
          const data = await refreshToken();
          setAccessToken(data.access_token);
          setUser(data.user);
        } catch (err) {
          setAccessToken(null);
          setUser(null);
        }
      },
      10 * 60 * 1000,
    );

    return () => clearInterval(interval);
  }, [user]);

  async function login(credential) {
    const data = await apiLogin(credential);
    setAccessToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function logout() {
    await apiLogout();
    setAccessToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
