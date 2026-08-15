import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ExternalLink, Search as SearchIcon } from "lucide-react";
import { useSearch, useSearchFilters } from "@/hooks/useSearch";
import { useApp } from "@/context/AppContext";
import { searchFormSchema, type SearchFormValues } from "@/lib/validation";
import { truncate } from "@/lib/utils";
import { ApiError } from "@/api/apiClient";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { Skeleton } from "@/components/common/LoadingState";
import { SaveSourceButton } from "@/components/sources/SaveSourceButton";
import type { SearchResult } from "@/types/search";

export function SearchPage() {
  const { sources, questionTypes } = useSearchFilters();
  const { preferences } = useApp();
  const search = useSearch();
  const [detail, setDetail] = useState<SearchResult | null>(null);

  const form = useForm<SearchFormValues>({
    resolver: zodResolver(searchFormSchema),
    defaultValues: { query: "", top_k: preferences.defaultTopK * 2, source: "", question_type: "" },
  });

  const onSubmit = form.handleSubmit((values) => {
    search.mutate({
      query: values.query,
      top_k: values.top_k,
      source: values.source || null,
      question_type: values.question_type || null,
      focus: values.focus || null,
    });
  });

  const results = search.data?.results ?? [];
  const errorMessage =
    search.error instanceof ApiError
      ? search.error.message
      : search.error
        ? "Something went wrong. Please try again."
        : form.formState.errors.query?.message ?? null;

  return (
    <div className="mx-auto h-full max-w-4xl overflow-y-auto px-4 py-6 md:px-8">
      <h1 className="text-lg font-semibold">Search Medical Knowledge</h1>
      <p className="mt-1 text-[13px] text-muted-foreground">
        Search the MedQuAD knowledge base directly by meaning, with filters.
      </p>

      <form onSubmit={onSubmit} className="mt-5 space-y-3" aria-label="Knowledge search">
        <div className="flex gap-2">
          <label htmlFor="kb-query" className="sr-only">Search query</label>
          <Input
            id="kb-query"
            placeholder="Search the MedQuAD knowledge base…"
            {...form.register("query")}
          />
          <Button type="submit" disabled={search.isPending}>
            <SearchIcon className="h-4 w-4" aria-hidden />
            Search
          </Button>
        </div>
        <div className="flex flex-wrap gap-2">
          <label className="sr-only" htmlFor="filter-source">Source filter</label>
          <Select id="filter-source" className="w-auto min-w-36" {...form.register("source")}>
            <option value="">All sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </Select>
          <label className="sr-only" htmlFor="filter-type">Question type filter</label>
          <Select id="filter-type" className="w-auto min-w-40" {...form.register("question_type")}>
            <option value="">All question types</option>
            {questionTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </Select>
          <label className="sr-only" htmlFor="filter-topk">Number of results</label>
          <Select id="filter-topk" className="w-auto" {...form.register("top_k")}>
            {[5, 10, 15, 20].map((n) => (
              <option key={n} value={n}>{n} results</option>
            ))}
          </Select>
        </div>
      </form>

      <div className="mt-6 space-y-3">
        {errorMessage && <ErrorMessage message={errorMessage} />}
        {search.isPending &&
          Array.from({ length: 3 }, (_, index) => <Skeleton key={index} className="h-28" />)}
        {search.isSuccess && results.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No records met the relevance threshold. Try different wording or fewer filters.
          </p>
        )}
        {results.map((result) => (
          <Card key={result.record_id + String(result.score)}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-[14px] font-semibold leading-snug">{result.question}</h2>
                {preferences.showScores && (
                  <span className="shrink-0 font-mono text-[11px] text-primary" title="Evidence relevance">
                    {(result.score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">
                {truncate(result.answer, 280)}
              </p>
              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                {result.source && <Badge variant="secondary">{result.source}</Badge>}
                {result.question_type && <Badge variant="outline">{result.question_type}</Badge>}
                {result.focus && <Badge variant="outline">{result.focus}</Badge>}
                <span className="flex-1" />
                <SaveSourceButton
                  source={{
                    record_id: result.record_id,
                    question: result.question,
                    source: result.source,
                    source_url: result.source_url,
                    focus: result.focus,
                    question_type: result.question_type,
                    answer_preview: truncate(result.answer, 200),
                  }}
                />
                <Button variant="outline" size="sm" onClick={() => setDetail(result)}>
                  View details
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog
        open={detail !== null}
        onClose={() => setDetail(null)}
        title={detail?.question ?? "Source details"}
        className="max-w-2xl"
      >
        {detail && (
          <div className="space-y-3 text-sm">
            <div className="flex flex-wrap gap-1.5">
              {detail.focus && <Badge>{detail.focus}</Badge>}
              {detail.question_type && <Badge variant="outline">{detail.question_type}</Badge>}
              {detail.source && <Badge variant="secondary">{detail.source}</Badge>}
              {preferences.showScores && (
                <Badge variant="outline">{(detail.score * 100).toFixed(0)}% relevance</Badge>
              )}
            </div>
            <p className="max-h-[45vh] overflow-y-auto whitespace-pre-wrap leading-relaxed text-foreground/90">
              {detail.answer}
            </p>
            {detail.source_url && (
              <a
                href={detail.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[13px] font-medium text-primary hover:underline"
              >
                View original source <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              </a>
            )}
          </div>
        )}
      </Dialog>
    </div>
  );
}
