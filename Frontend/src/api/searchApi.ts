import { request } from "./apiClient";
import type {
  QuestionTypesResponse,
  SearchRequest,
  SearchResponse,
  SourcesResponse,
  StatisticsResponse,
} from "@/types/search";

export function searchKnowledge(body: SearchRequest, signal?: AbortSignal): Promise<SearchResponse> {
  return request<SearchResponse>("/api/v1/search", { method: "POST", body, signal });
}

export function fetchSources(): Promise<SourcesResponse> {
  return request<SourcesResponse>("/api/v1/sources");
}

export function fetchQuestionTypes(): Promise<QuestionTypesResponse> {
  return request<QuestionTypesResponse>("/api/v1/question-types");
}

export function fetchStatistics(): Promise<StatisticsResponse> {
  return request<StatisticsResponse>("/api/v1/statistics");
}
