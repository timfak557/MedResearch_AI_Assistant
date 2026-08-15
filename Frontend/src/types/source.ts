/** A cited source attached to a chat answer (backend ChatSource). */
export interface Source {
  id: number;
  record_id: string;
  question: string;
  source?: string;
  source_url?: string;
  focus?: string;
  score?: number;
}

/** A source the user saved locally. */
export interface SavedSource {
  record_id: string;
  question: string;
  source?: string;
  source_url?: string;
  focus?: string;
  question_type?: string;
  answer_preview?: string;
  saved_at: string; // ISO date
}
