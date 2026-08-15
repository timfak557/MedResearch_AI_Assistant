import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { ChevronDown, ChevronUp, Eraser, Plus } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { useApp } from "@/context/AppContext";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { TypingIndicator } from "@/components/common/LoadingState";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { SourcePanel } from "@/components/sources/SourcePanel";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Conversation } from "@/types/conversation";

export function ChatPage() {
  const {
    messages, isLoading, error, sendMessage, regenerate,
    newConversation, openConversation, setFeedback, lastAssistantMessage,
  } = useChat();
  const { preferences } = useApp();
  const location = useLocation();

  const [highlightedSource, setHighlightedSource] = useState<number | null>(null);
  const [mobileEvidenceOpen, setMobileEvidenceOpen] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);
  const openedFromHistory = useRef(false);

  // Reopen a conversation passed from the History page.
  useEffect(() => {
    const state = location.state as { conversation?: Conversation } | null;
    if (state?.conversation && !openedFromHistory.current) {
      openedFromHistory.current = true;
      openConversation(state.conversation);
    }
  }, [location.state, openConversation]);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, isLoading]);

  const sources = lastAssistantMessage?.response?.sources ?? [];
  const onCitationClick = useCallback((id: number) => {
    setMobileEvidenceOpen(true);
    setHighlightedSource(id);
  }, []);

  return (
    <div className="flex h-full">
      {/* main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* chat header */}
        <header className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5 md:px-6">
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold">MedResearch AI</h1>
            <p className="flex items-center gap-2 text-[11px] text-muted-foreground">
              AI Medical Research Assistant
              <Badge variant="secondary">Knowledge Base: MedQuAD</Badge>
            </p>
          </div>
          <div className="flex shrink-0 gap-1.5">
            <Button variant="outline" size="sm" onClick={newConversation}>
              <Plus className="h-3.5 w-3.5" aria-hidden /> New
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={newConversation}
              disabled={messages.length === 0}
              aria-label="Clear conversation"
            >
              <Eraser className="h-3.5 w-3.5" aria-hidden />
              <span className="hidden sm:inline">Clear</span>
            </Button>
          </div>
        </header>

        {/* thread */}
        <div ref={threadRef} className="min-h-0 flex-1 overflow-y-auto">
          {messages.length === 0 && !isLoading ? (
            <WelcomeScreen onExampleClick={sendMessage} />
          ) : (
            <div
              className={`mx-auto flex max-w-3xl flex-col px-4 py-5 md:px-6 ${
                preferences.compactMode ? "gap-3" : "gap-5"
              }`}
            >
              {messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onCitationClick={onCitationClick}
                  onRegenerate={regenerate}
                  onFeedback={setFeedback}
                  isLatest={index === messages.length - 1 && message.role === "assistant"}
                />
              ))}
              {isLoading && <TypingIndicator />}
              {error && <ErrorMessage message={error} />}
            </div>
          )}
        </div>

        {/* mobile evidence toggle */}
        {preferences.showEvidence && sources.length > 0 && (
          <button
            type="button"
            className="flex items-center justify-center gap-1.5 border-t border-border py-2 text-xs font-medium text-muted-foreground xl:hidden"
            onClick={() => setMobileEvidenceOpen((open) => !open)}
            aria-expanded={mobileEvidenceOpen}
          >
            {mobileEvidenceOpen ? (
              <ChevronDown className="h-3.5 w-3.5" aria-hidden />
            ) : (
              <ChevronUp className="h-3.5 w-3.5" aria-hidden />
            )}
            Evidence ({sources.length})
          </button>
        )}
        {preferences.showEvidence && mobileEvidenceOpen && sources.length > 0 && (
          <div className="max-h-[45vh] overflow-y-auto border-t border-border xl:hidden">
            <SourcePanel
              sources={sources}
              highlightedId={highlightedSource}
              onHighlightHandled={() => setHighlightedSource(null)}
            />
          </div>
        )}

        <ChatInput onSend={sendMessage} disabled={isLoading} />
      </div>

      {/* desktop evidence panel */}
      {preferences.showEvidence && (
        <aside className="hidden w-80 shrink-0 border-l border-border xl:block">
          <SourcePanel
            sources={sources}
            highlightedId={highlightedSource}
            onHighlightHandled={() => setHighlightedSource(null)}
          />
        </aside>
      )}
    </div>
  );
}
