import { AlertTriangle, ShieldAlert } from "lucide-react";
import type { SafetyCategory } from "@/types/chat";

interface SafetyNoticeProps {
  category: SafetyCategory | undefined;
}

/** Category-specific medical limitation notices (spec §20). */
export function SafetyNotice({ category }: SafetyNoticeProps) {
  if (!category) return null;

  if (category === "emergency" || category === "self_harm") {
    return (
      <div
        role="alert"
        className="mt-3 flex items-start gap-2.5 rounded-lg border border-destructive/40 bg-[hsl(var(--destructive)/0.08)] p-3 text-[13px] leading-relaxed text-destructive"
      >
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <span>
          MedResearch AI is not an emergency service. If this is an emergency, contact your
          local emergency services immediately.
        </span>
      </div>
    );
  }

  const messages: Partial<Record<string, string>> = {
    diagnosis_request:
      "MedResearch AI provides educational medical information and cannot diagnose medical conditions.",
    medication_request:
      "Medication decisions should be discussed with a qualified healthcare professional.",
    treatment_request:
      "Treatment decisions should be discussed with a qualified healthcare professional.",
  };
  const message = messages[category];
  if (!message) return null;

  return (
    <div
      role="note"
      className="mt-3 flex items-start gap-2.5 rounded-lg border border-[hsl(var(--warning)/0.4)] bg-[hsl(var(--warning)/0.08)] p-3 text-[13px] leading-relaxed text-[hsl(var(--warning))]"
    >
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
      <span>{message}</span>
    </div>
  );
}
