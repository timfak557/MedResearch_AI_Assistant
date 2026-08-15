import { Bookmark, BookmarkCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useApp } from "@/context/AppContext";
import type { SavedSource } from "@/types/source";

interface SaveSourceButtonProps {
  source: Omit<SavedSource, "saved_at">;
}

export function SaveSourceButton({ source }: SaveSourceButtonProps) {
  const { toggleSavedSource, isSourceSaved } = useApp();
  const saved = isSourceSaved(source.record_id);
  return (
    <Button
      variant="ghost"
      size="sm"
      aria-pressed={saved}
      aria-label={saved ? "Remove from saved sources" : "Save source"}
      onClick={() => toggleSavedSource({ ...source, saved_at: new Date().toISOString() })}
      className="text-muted-foreground"
    >
      {saved ? (
        <BookmarkCheck className="h-3.5 w-3.5 text-primary" aria-hidden />
      ) : (
        <Bookmark className="h-3.5 w-3.5" aria-hidden />
      )}
      {saved ? "Saved" : "Save"}
    </Button>
  );
}
