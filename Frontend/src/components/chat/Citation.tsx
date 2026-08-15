interface CitationProps {
  id: number;
  onClick: (id: number) => void;
}

/** Interactive inline citation marker, e.g. [1]. */
export function Citation({ id, onClick }: CitationProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(id)}
      aria-label={`View source ${id}`}
      className="mx-0.5 inline-flex h-[18px] min-w-[18px] items-center justify-center rounded border border-primary/40 bg-accent px-1 align-[2px] font-mono text-[10px] font-semibold text-accent-foreground transition-colors hover:bg-primary hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    >
      {id}
    </button>
  );
}
