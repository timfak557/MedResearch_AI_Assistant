import { useEffect, useState } from "react";
import { FileSearch } from "lucide-react";
import { SourceCard } from "./SourceCard";
import type { Source } from "@/types/source";

interface SourcePanelProps {
  sources: Source[];
  highlightedId: number | null;
  onHighlightHandled: () => void;
}

/** Evidence panel — updates after every query, flashes the cited source. */
export function SourcePanel({ sources, highlightedId, onHighlightHandled }: SourcePanelProps) {
  const [flashId, setFlashId] = useState<number | null>(null);

  useEffect(() => {
    if (highlightedId === null) return;
    setFlashId(highlightedId);
    document
      .getElementById(`source-${highlightedId}`)
      ?.scrollIntoView({ behavior: "smooth", block: "center" });
    const timer = setTimeout(() => {
      setFlashId(null);
      onHighlightHandled();
    }, 1800);
    return () => clearTimeout(timer);
  }, [highlightedId, onHighlightHandled]);

  return (
    <div aria-label="Evidence sources" className="flex h-full flex-col">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Evidence</h2>
        <p className="text-[11.5px] text-muted-foreground">
          {sources.length > 0
            ? `${sources.length} source${sources.length === 1 ? "" : "s"} found`
            : "Sources appear here after each answer"}
        </p>
      </div>
      <div className="flex-1 space-y-2.5 overflow-y-auto p-3">
        {sources.length === 0 ? (
          <div className="mt-10 flex flex-col items-center gap-2 text-center text-muted-foreground">
            <FileSearch className="h-7 w-7 opacity-50" aria-hidden />
            <p className="max-w-[200px] text-xs leading-relaxed">
              Ask a question and the retrieved MedQuAD evidence will be listed here with
              relevance scores.
            </p>
          </div>
        ) : (
          sources.map((source) => (
            <SourceCard key={source.id} source={source} highlighted={flashId === source.id} />
          ))
        )}
      </div>
    </div>
  );
}
