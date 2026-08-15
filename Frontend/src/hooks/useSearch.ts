import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchQuestionTypes, fetchSources, fetchStatistics, searchKnowledge } from "@/api/searchApi";
import type { SearchRequest } from "@/types/search";

export function useSearchFilters() {
  const sources = useQuery({
    queryKey: ["sources"],
    queryFn: fetchSources,
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });
  const questionTypes = useQuery({
    queryKey: ["question-types"],
    queryFn: fetchQuestionTypes,
    staleTime: 10 * 60 * 1000,
    retry: 1,
  });
  return {
    sources: sources.data?.sources ?? [],
    questionTypes: questionTypes.data?.question_types ?? [],
  };
}

export function useStatistics() {
  return useQuery({
    queryKey: ["statistics"],
    queryFn: fetchStatistics,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}

export function useSearch() {
  return useMutation({
    mutationFn: (requestBody: SearchRequest) => searchKnowledge(requestBody),
  });
}
