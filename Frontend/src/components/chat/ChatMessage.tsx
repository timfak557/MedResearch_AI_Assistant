import { Check, Copy, RefreshCw, ThumbsDown, ThumbsUp } from "lucide-react";
import { useState } from "react";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { SafetyNotice } from "@/components/safety/SafetyNotice";
import { Disclaimer } from "@/components/safety/Disclaimer";
import { ConfidenceBadge } from "@/components/common/ConfidenceBadge";
import { Button } from "@/components/ui/button";
import { splitDisclaimer } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

interface ChatMessageProps {
  message: ChatMessageType;
  onCitationClick: (id: number) => void;
  onRegenerate: () => void;
  onFeedback: (messageId: string, feedback: "helpful" | "not_helpful") => void;
  isLatest: boolean;
}

export function ChatMessage({
  message,
  onCitationClick,
  onRegenerate,
  onFeedback,
  isLatest,
}: ChatMessageProps) {
  const [copied, setCopied] = useState(false);

  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-fade-up">
        <div className="max-w-[85%] rounded-xl rounded-br-sm bg-primary px-4 py-2.5 text-sm leading-relaxed text-primary-foreground md:max-w-[70%]">
          {message.content}
        </div>
      </div>
    );
  }

  const response = message.response;
  const insufficient = response?.insufficient_context === true;
  const { body, disclaimer } = splitDisclaimer(message.content);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className="flex justify-start animate-fade-up">
      <div className="w-full max-w-[95%] md:max-w-[85%]">
        <div
          className={cn(
            "rounded-xl rounded-bl-sm border border-border bg-card px-4 py-3",
            insufficient && "border-[hsl(var(--warning)/0.5)]",
          )}
        >
          {insufficient && (
            <p className="mb-2 text-[13px] font-medium text-[hsl(var(--warning))]">
              Not enough evidence found — try asking your question differently or search the
              medical knowledge base directly.
            </p>
          )}
          <AnswerMarkdown markdown={body} onCitationClick={onCitationClick} />
          <SafetyNotice category={response?.safety_category} />
          <Disclaimer text={disclaimer ?? response?.disclaimer} />
        </div>

        <div className="mt-1.5 flex flex-wrap items-center gap-1.5 px-1">
          {response?.retrieval_count !== undefined && response.retrieval_count > 0 && (
            <span className="text-[11px] text-muted-foreground">
              {response.retrieval_count} sources retrieved
            </span>
          )}
          <ConfidenceBadge confidence={response?.confidence} />
          <span className="flex-1" />
          <Button variant="ghost" size="sm" onClick={copy} aria-label="Copy answer">
            {copied ? <Check className="h-3.5 w-3.5" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
          </Button>
          {isLatest && (
            <Button variant="ghost" size="sm" onClick={onRegenerate} aria-label="Regenerate answer">
              <RefreshCw className="h-3.5 w-3.5" aria-hidden />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            aria-label="Mark answer helpful"
            aria-pressed={message.feedback === "helpful"}
            onClick={() => onFeedback(message.id, "helpful")}
            className={message.feedback === "helpful" ? "text-[hsl(var(--success))]" : ""}
          >
            <ThumbsUp className="h-3.5 w-3.5" aria-hidden />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Mark answer not helpful"
            aria-pressed={message.feedback === "not_helpful"}
            onClick={() => onFeedback(message.id, "not_helpful")}
            className={message.feedback === "not_helpful" ? "text-destructive" : ""}
          >
            <ThumbsDown className="h-3.5 w-3.5" aria-hidden />
          </Button>
        </div>
      </div>
    </div>
  );
}
