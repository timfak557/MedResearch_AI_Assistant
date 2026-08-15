export interface SearchRequest {
  query: string;
  top_k?: number;
  source?: string | null;
  focus?: string | null;
  question_type?: string | null;
}

export interface SearchResult {
  record_id: string;
  question: string;
  answer: string;
  source?: string;
  source_url?: string;
  focus?: string;
  question_type?: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

export interface SourcesResponse {
  sources: string[];
}

export interface QuestionTypesResponse {
  question_types: string[];
}

export interface StatisticsResponse {
  collection?: string;
  total_chunks?: number;
  sources?: number;
  question_types?: number;
  embedding_model?: string;
  qdrant_healthy?: boolean;
}
