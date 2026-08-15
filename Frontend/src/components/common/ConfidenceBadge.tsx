import { Info } from "lucide-react";

interface ConfidenceBadgeProps {
  confidence: number | undefined;
}

const TOOLTIP =
  "This represents how strongly the retrieved knowledge matches your question. It is not a measure of medical accuracy.";

/** Retrieval-confidence indicator — carefully labeled (spec §22). */
export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  if (confidence === undefined || confidence <= 0) return null;
  const percent = Math.round(confidence * 100);
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] text-muted-foreground"
      title={TOOLTIP}
    >
      Retrieval confidence
      <span
        role="meter"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Retrieval confidence ${percent} percent`}
        className="inline-block h-1.5 w-14 overflow-hidden rounded-full bg-muted"
      >
        <span className="block h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
      </span>
      {percent}%
      <Info className="h-3 w-3" aria-hidden />
    </span>
  );
}
