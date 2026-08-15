import { FlaskConical } from "lucide-react";

const EXAMPLE_QUESTIONS = [
  "What are the symptoms of diabetes?",
  "What are the risk factors for heart disease?",
  "What treatments are available for asthma?",
  "What are the complications associated with hypertension?",
];

interface WelcomeScreenProps {
  onExampleClick: (question: string) => void;
}

export function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
  return (
    <div className="mx-auto flex h-full max-w-xl flex-col items-center justify-center gap-5 px-6 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-xl bg-accent text-accent-foreground">
        <FlaskConical className="h-6 w-6" aria-hidden />
      </span>
      <div>
        <h1 className="text-xl font-semibold md:text-2xl">
          How can I help with your medical research?
        </h1>
        <p className="mt-2 text-[13.5px] leading-relaxed text-muted-foreground">
          Ask questions about medical conditions, symptoms, treatments, research topics, and
          other information available in the MedQuAD knowledge base.
        </p>
      </div>
      <div className="grid w-full gap-2 sm:grid-cols-2">
        {EXAMPLE_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onExampleClick(question)}
            className="rounded-xl border border-border bg-card px-4 py-3 text-left text-[13px] leading-snug text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
