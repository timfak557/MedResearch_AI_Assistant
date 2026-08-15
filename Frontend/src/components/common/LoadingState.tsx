export function TypingIndicator() {
  return (
    <div
      role="status"
      aria-label="MedResearch AI is preparing a response"
      className="flex items-center gap-2.5 text-sm text-muted-foreground"
    >
      <span className="flex gap-1" aria-hidden>
        <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse2" />
        <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse2 [animation-delay:0.2s]" />
        <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse2 [animation-delay:0.4s]" />
      </span>
      {/* The backend performs retrieval + generation in one call; we show one
          honest combined stage rather than simulating separate events. */}
      Searching medical knowledge and generating a grounded response…
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-muted ${className ?? ""}`} aria-hidden />;
}
