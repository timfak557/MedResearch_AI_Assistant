import { useNavigate } from "react-router-dom";
import { History, Trash2 } from "lucide-react";
import { useConversations } from "@/hooks/useConversations";
import { formatDate, truncate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function HistoryPage() {
  const { conversations, deleteOne, clearAllConversations } = useConversations();
  const navigate = useNavigate();

  return (
    <div className="mx-auto h-full max-w-3xl overflow-y-auto px-4 py-6 md:px-8">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">Research History</h1>
          <p className="mt-1 text-[13px] text-muted-foreground">
            Stored on this device only. Reopen a session to continue where you left off.
          </p>
        </div>
        {conversations.length > 0 && (
          <Button variant="outline" size="sm" onClick={clearAllConversations}>
            Clear all
          </Button>
        )}
      </div>

      <div className="mt-5 space-y-2.5">
        {conversations.length === 0 && (
          <div className="mt-16 flex flex-col items-center gap-2 text-center text-muted-foreground">
            <History className="h-7 w-7 opacity-50" aria-hidden />
            <p className="text-sm">No research sessions yet.</p>
            <p className="text-xs">Start a conversation and it will appear here.</p>
          </div>
        )}
        {conversations.map((conversation) => (
          <Card key={conversation.id} className="transition-shadow hover:shadow-md">
            <CardContent className="flex items-center gap-3 p-3.5">
              <button
                type="button"
                className="min-w-0 flex-1 text-left focus-visible:outline-none"
                onClick={() => navigate("/", { state: { conversation } })}
                aria-label={`Reopen research session: ${conversation.title}`}
              >
                <div className="truncate text-[14px] font-medium">{conversation.title}</div>
                <div className="mt-0.5 text-[12px] text-muted-foreground">
                  {formatDate(conversation.updatedAt)} ·{" "}
                  {truncate(conversation.lastQuestion, 80)}
                </div>
              </button>
              <Button
                variant="ghost"
                size="icon"
                aria-label={`Delete session: ${conversation.title}`}
                onClick={() => void deleteOne(conversation.id)}
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" aria-hidden />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
