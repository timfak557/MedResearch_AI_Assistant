,import { useMemo, useState } from "react";
import { Bookmark, ExternalLink, Trash2 } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { formatDate } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function SavedSourcesPage() {
  const { savedSources, toggleSavedSource } = useApp();
  const [filter, setFilter] = useState("");

  const visible = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return savedSources;
    return savedSources.filter((source) =>
      [source.question, source.focus, source.source]
        .filter(Boolean)
        .some((field) => field!.toLowerCase().includes(query)),
    );
  }, [savedSources, filter]);

  return (
    <div className="mx-auto h-full max-w-3xl overflow-y-auto px-4 py-6 md:px-8">
      <h1 className="text-lg font-semibold">Saved Sources</h1>
      <p className="mt-1 text-[13px] text-muted-foreground">
        Evidence you bookmarked from answers and knowledge search.
      </p>

      <div className="mt-4">
        <label htmlFor="saved-filter" className="sr-only">Search saved sources</label>
        <Input
          id="saved-filter"
          placeholder="Search saved sources…"
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        />
      </div>

      <div className="mt-4 space-y-2.5">
        {visible.length === 0 && (
          <div className="mt-16 flex flex-col items-center gap-2 text-center text-muted-foreground">
            <Bookmark className="h-7 w-7 opacity-50" aria-hidden />
            <p className="text-sm">
              {savedSources.length === 0 ? "No saved sources yet." : "No matches."}
            </p>
          </div>
        )}
        {visible.map((source) => (
          <Card key={source.record_id}>
            <CardContent className="p-3.5">
              <div className="flex items-start justify-between gap-3">
                <p className="text-[14px] font-medium leading-snug">{source.question}</p>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Remove saved source"
                  onClick={() => toggleSavedSource(source)}
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground" aria-hidden />
                </Button>
              </div>
              {source.answer_preview && (
                <p className="mt-1 text-[12.5px] leading-relaxed text-muted-foreground">
                  {source.answer_preview}
                </p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                {source.source && <Badge variant="secondary">{source.source}</Badge>}
                {source.focus && <Badge variant="outline">{source.focus}</Badge>}
                <span className="text-[11px] text-muted-foreground">
                  Saved {formatDate(source.saved_at)}
                </span>
                <span className="flex-1" />
                {source.source_url && (
                  <a
                    href={source.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[12px] font-medium text-primary hover:underline"
                  >
                    Open source <ExternalLink className="h-3 w-3" aria-hidden />
                  </a>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
