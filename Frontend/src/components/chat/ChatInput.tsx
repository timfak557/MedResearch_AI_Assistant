import { useRef, useState, type KeyboardEvent } from "react";
import { SendHorizonal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MAX_QUERY_LENGTH } from "@/lib/validation";

interface ChatInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-border bg-background p-3 md:px-6 md:py-4">
      <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-xl border border-input bg-card p-2 pl-3.5 focus-within:ring-2 focus-within:ring-primary">
        <label htmlFor="chat-input" className="sr-only">
          Ask a medical research question
        </label>
        <textarea
          id="chat-input"
          ref={textareaRef}
          rows={1}
          value={value}
          maxLength={MAX_QUERY_LENGTH}
          placeholder="Ask a medical research question…"
          onChange={(event) => {
            setValue(event.target.value);
            event.target.style.height = "auto";
            event.target.style.height = `${Math.min(event.target.scrollHeight, 140)}px`;
          }}
          onKeyDown={onKeyDown}
          className="max-h-[140px] flex-1 resize-none bg-transparent py-1.5 text-sm leading-relaxed outline-none placeholder:text-muted-foreground"
        />
        <Button
          size="icon"
          onClick={submit}
          disabled={disabled || value.trim().length === 0}
          aria-label="Send question"
        >
          <SendHorizonal className="h-4 w-4" aria-hidden />
        </Button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[10.5px] text-muted-foreground">
        Educational information only — consult a qualified healthcare professional for personal
        medical decisions.
      </p>
    </div>
  );
}
