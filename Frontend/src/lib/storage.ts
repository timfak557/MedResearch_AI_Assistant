/** Typed localStorage helpers.
 *
 * Conversation transcripts are stored locally ONLY because Research History
 * is an explicit product feature (spec §23), and storage can be disabled in
 * Settings. Nothing here ever contains API keys or backend secrets.
 */

import type { Conversation } from "@/types/conversation";
import type { SavedSource } from "@/types/source";

const KEYS = {
  conversations: "medresearch.conversations.v1",
  savedSources: "medresearch.savedSources.v1",
  preferences: "medresearch.preferences.v1",
  theme: "medresearch.theme.v1",
} as const;

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage full or unavailable — history is a best-effort feature */
  }
}

/* ── conversations ── */
const MAX_STORED_CONVERSATIONS = 50;

export function loadConversations(): Conversation[] {
  return read<Conversation[]>(KEYS.conversations, []);
}

export function saveConversations(conversations: Conversation[]): void {
  write(KEYS.conversations, conversations.slice(0, MAX_STORED_CONVERSATIONS));
}

export function clearConversations(): void {
  localStorage.removeItem(KEYS.conversations);
}

/* ── saved sources ── */
export function loadSavedSources(): SavedSource[] {
  return read<SavedSource[]>(KEYS.savedSources, []);
}

export function saveSavedSources(sources: SavedSource[]): void {
  write(KEYS.savedSources, sources);
}

/* ── preferences ── */
export interface Preferences {
  defaultTopK: number;
  showEvidence: boolean;
  showScores: boolean;
  compactMode: boolean;
  storeHistory: boolean;
}

export const DEFAULT_PREFERENCES: Preferences = {
  defaultTopK: 5,
  showEvidence: true,
  showScores: true,
  compactMode: false,
  storeHistory: true,
};

export function loadPreferences(): Preferences {
  return { ...DEFAULT_PREFERENCES, ...read<Partial<Preferences>>(KEYS.preferences, {}) };
}

export function savePreferences(preferences: Preferences): void {
  write(KEYS.preferences, preferences);
}

/* ── theme ── */
export type Theme = "light" | "dark" | "system";

export function loadTheme(): Theme {
  return read<Theme>(KEYS.theme, "system");
}

export function saveTheme(theme: Theme): void {
  write(KEYS.theme, theme);
}
