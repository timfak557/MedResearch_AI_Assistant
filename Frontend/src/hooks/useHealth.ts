import { useQuery } from "@tanstack/react-query";
import { fetchSystemStatus } from "@/api/healthApi";
import type { SystemStatus } from "@/types/health";

const CHECKING: SystemStatus = {
  api: "checking",
  qdrant: "checking",
  embeddingModel: "checking",
  llm: "checking",
};

/** Polls /ready at a modest interval (30 s) — never aggressively. */
export function useHealth(): SystemStatus {
  const query = useQuery({
    queryKey: ["system-status"],
    queryFn: fetchSystemStatus,
    refetchInterval: 30_000,
    refetchOnWindowFocus: false,
    retry: false,
  });
  return query.data ?? CHECKING;
}
