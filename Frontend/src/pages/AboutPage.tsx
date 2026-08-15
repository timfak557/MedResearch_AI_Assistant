import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const TECHNOLOGY = ["RAG", "Qdrant", "LLM", "MCP", "FastAPI", "MedQuAD"];

export function AboutPage() {
  return (
    <div className="mx-auto h-full max-w-2xl space-y-4 overflow-y-auto px-4 py-6 md:px-8">
      <h1 className="text-lg font-semibold">About MedResearch AI</h1>

      <Card>
        <CardContent className="pt-4 text-[13.5px] leading-relaxed">
          MedResearch AI is an AI-powered medical research assistant that uses
          retrieval-augmented generation and the MedQuAD knowledge base to provide
          evidence-grounded educational information. Every answer is composed only from
          retrieved evidence published by National Institutes of Health sources, and carries
          citations you can inspect.
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Technology</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-1.5">
          {TECHNOLOGY.map((item) => <Badge key={item} variant="secondary">{item}</Badge>)}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Important</CardTitle></CardHeader>
        <CardContent>
          <ul className="list-disc space-y-1.5 pl-5 text-[13.5px] leading-relaxed text-muted-foreground">
            <li>This application is not a doctor.</li>
            <li>It does not diagnose medical conditions.</li>
            <li>It does not prescribe medication.</li>
            <li>It is for educational and research purposes only.</li>
            <li>
              For personal medical decisions, always consult a qualified healthcare
              professional.
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
