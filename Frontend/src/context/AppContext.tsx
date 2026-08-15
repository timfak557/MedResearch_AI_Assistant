/* Global client state: theme, preferences, conversations, saved sources.
 * Server state (chat calls, search, health) lives in TanStack Query. */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Conversation } from "@/types/conversation";
import type { SavedSource } from "@/types/source";
import {
  DEFAULT_PREFERENCES,
  loadConversations,
  loadPreferences,
  loadSavedSources,
  loadTheme,
  saveConversations,
  savePreferences,
  saveSavedSources,
  saveTheme,
  clearConversations,
  type Preferences,
  type Theme,
} from "@/lib/storage";

interface AppContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  preferences: Preferences;
  updatePreferences: (patch: Partial<Preferences>) => void;

  conversations: Conversation[];
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  upsertConversation: (conversation: Conversation) => void;
  removeConversation: (id: string) => void;
  clearAllConversations: () => void;

  savedSources: SavedSource[];
  toggleSavedSource: (source: SavedSource) => void;
  isSourceSaved: (recordId: string) => boolean;

  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

function applyTheme(theme: Theme) {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = theme === "dark" || (theme === "system" && prefersDark);
  document.documentElement.classList.toggle("dark", dark);
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => loadTheme());
  const [preferences, setPreferences] = useState<Preferences>(() => loadPreferences());
  const [conversations, setConversations] = useState<Conversation[]>(() => loadConversations());
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [savedSources, setSavedSources] = useState<SavedSource[]>(() => loadSavedSources());
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    applyTheme(theme);
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyTheme("system");
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
    saveTheme(next);
  }, []);

  const updatePreferences = useCallback((patch: Partial<Preferences>) => {
    setPreferences((previous) => {
      const next = { ...previous, ...patch };
      savePreferences(next);
      return next;
    });
  }, []);

  const upsertConversation = useCallback(
    (conversation: Conversation) => {
      setConversations((previous) => {
        const rest = previous.filter((c) => c.id !== conversation.id);
        const next = [conversation, ...rest];
        if (preferences.storeHistory) saveConversations(next);
        return next;
      });
    },
    [preferences.storeHistory],
  );

  const removeConversation = useCallback((id: string) => {
    setConversations((previous) => {
      const next = previous.filter((c) => c.id !== id);
      saveConversations(next);
      return next;
    });
    setActiveConversationId((current) => (current === id ? null : current));
  }, []);

  const clearAllConversations = useCallback(() => {
    setConversations([]);
    clearConversations();
    setActiveConversationId(null);
  }, []);

  const toggleSavedSource = useCallback((source: SavedSource) => {
    setSavedSources((previous) => {
      const exists = previous.some((s) => s.record_id === source.record_id);
      const next = exists
        ? previous.filter((s) => s.record_id !== source.record_id)
        : [{ ...source, saved_at: new Date().toISOString() }, ...previous];
      saveSavedSources(next);
      return next;
    });
  }, []);

  const isSourceSaved = useCallback(
    (recordId: string) => savedSources.some((s) => s.record_id === recordId),
    [savedSources],
  );

  const value = useMemo<AppContextValue>(
    () => ({
      theme,
      setTheme,
      preferences,
      updatePreferences,
      conversations,
      activeConversationId,
      setActiveConversationId,
      upsertConversation,
      removeConversation,
      clearAllConversations,
      savedSources,
      toggleSavedSource,
      isSourceSaved,
      sidebarOpen,
      setSidebarOpen,
    }),
    [
      theme, setTheme, preferences, updatePreferences, conversations,
      activeConversationId, upsertConversation, removeConversation,
      clearAllConversations, savedSources, toggleSavedSource, isSourceSaved,
      sidebarOpen,
    ],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) throw new Error("useApp must be used within AppProvider");
  return context;
}

export { DEFAULT_PREFERENCES };
