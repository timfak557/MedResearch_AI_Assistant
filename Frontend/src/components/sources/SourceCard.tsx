import { ExternalLink } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SaveSourceButton } from "./SaveSourceButton";
import { useApp } from "@/context/AppContext";
import type { Source } from "@/types/source";
import { cn } from "@/lib/utils";

interface SourceCardProps {
  source: Source;
  highlighted?: boolean;
  onSelect?: (id: number) => void;
}

export function SourceCard({ source, highlighted, onSelect }: SourceCardProps) {
  const { preferences } = useApp();
  const percent = source.score !== undefined ? Math.round(source.score * 100) : null;

  return (
    <Card
      id={`source-${source.id}`}
      role={onSelect ? "button" : undefined}
      tabIndex={onSelect ? 0 : undefined}
      onClick={() => onSelect?.(source.id)}
      onKeyDown={(event) => {
        if (onSelect && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          onSelect(source.id);
        }
      }}
      className={cn(
        "transition-shadow",
        onSelect && "cursor-pointer hover:shadow-md focus-visible:ring-2 focus-visible:ring-primary",
        highlighted && "ring-2 ring-primary",
      )}
    >
      <CardContent className="p-3.5">
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <span className="font-mono text-[10.5px] font-semibold text-primary">
            Source [{source.id}]
          </span>
          {percent !== null && preferences.showScores && (
            <span className="font-mono text-[10.5px] text-muted-foreground" title="Evidence relevance">
              {percent}% relevance
            </span>
          )}
        </div>
        <p className="text-[13px] font-medium leading-snug">{source.question}</p>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {source.source && <Badge variant="secondary">{source.source}</Badge>}
          {source.focus && <Badge variant="outline">{source.focus}</Badge>}
        </div>
        <div className="mt-2 flex items-center justify-between gap-2">
          <SaveSourceButton
            source={{
              record_id: source.record_id,
              question: source.question,
              source: source.source,
              source_url: source.source_url,
              focus: source.focus,
            }}
          />
          {source.source_url && (
            <a
              href={source.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(event) => event.stopPropagation()}
              className="inline-flex items-center gap-1 text-[11.5px] font-medium text-primary hover:underline"
            >
              View source <ExternalLink className="h-3 w-3" aria-hidden />
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
