import { useHealth } from "@/hooks/useHealth";
import type { ServiceState } from "@/types/health";
import { cn } from "@/lib/utils";

const LABELS: Array<{ key: keyof ReturnType<typeof useHealth>; label: string }> = [
  { key: "api", label: "API" },
  { key: "qdrant", label: "Qdrant" },
  { key: "embeddingModel", label: "Embedding" },
  { key: "llm", label: "LLM" },
];

function stateText(state: ServiceState): string {
  if (state === "connected") return "Connected";
  if (state === "unavailable") return "Unavailable";
  return "Checking";
}

export function SystemStatus() {
  const status = useHealth();
  return (
    <div aria-label="System status" className="space-y-1.5 text-[11px]">
      <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        System status
      </div>
      {LABELS.map(({ key, label }) => {
        const state = status[key];
        return (
          <div key={key} className="flex items-center justify-between text-muted-foreground">
            <span>{label}</span>
            <span className="inline-flex items-center gap-1.5">
              <span
                aria-hidden
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  state === "connected" && "bg-[hsl(var(--success))]",
                  state === "unavailable" && "bg-destructive",
                  state === "checking" && "bg-muted-foreground animate-pulse2",
                )}
              />
              {stateText(state)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
