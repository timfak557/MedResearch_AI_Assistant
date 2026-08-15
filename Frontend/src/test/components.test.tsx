import { describe, expect, it, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "./helpers";
import { AnswerMarkdown } from "@/components/chat/AnswerMarkdown";
import { Citation } from "@/components/chat/Citation";
import { SafetyNotice } from "@/components/safety/SafetyNotice";
import { Disclaimer } from "@/components/safety/Disclaimer";
import { ConfidenceBadge } from "@/components/common/ConfidenceBadge";
import { SourceCard } from "@/components/sources/SourceCard";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { ChatInput } from "@/components/chat/ChatInput";
import type { Source } from "@/types/source";

const SOURCE: Source = {
  id: 1,
  record_id: "rec-1",
  question: "What are the symptoms of diabetes?",
  source: "NIHSeniorHealth",
  source_url: "https://example.org/diabetes",
  focus: "Diabetes",
  score: 0.87,
};

describe("Citation", () => {
  it("renders the citation number and fires onClick", () => {
    const onClick = vi.fn();
    renderWithProviders(<Citation id={2} onClick={onClick} />);
    const button = screen.getByRole("button", { name: /view source 2/i });
    fireEvent.click(button);
    expect(onClick).toHaveBeenCalledWith(2);
  });
});

describe("AnswerMarkdown", () => {
  it("renders markdown and converts [n] markers into interactive citations", () => {
    const onClick = vi.fn();
    renderWithProviders(
      <AnswerMarkdown
        markdown={"**Symptoms** include thirst [1] and fatigue [2, 3]."}
        onCitationClick={onClick}
      />,
    );
    expect(screen.getByText("Symptoms")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /view source 1/i }));
    expect(onClick).toHaveBeenCalledWith(1);
    expect(screen.getByRole("button", { name: /view source 3/i })).toBeInTheDocument();
  });

  it("does not render raw HTML from the answer", () => {
    renderWithProviders(
      <AnswerMarkdown markdown={'<img src=x onerror="window.hacked=1">text'} onCitationClick={() => {}} />,
    );
    expect(document.querySelector("img")).toBeNull();
  });
});

describe("SafetyNotice", () => {
  it("shows the diagnosis limitation notice", () => {
    renderWithProviders(<SafetyNotice category="diagnosis_request" />);
    expect(screen.getByText(/cannot diagnose medical conditions/i)).toBeInTheDocument();
  });

  it("shows a prominent emergency warning without inventing phone numbers", () => {
    renderWithProviders(<SafetyNotice category="emergency" />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(/not an emergency service/i);
    expect(alert.textContent).not.toMatch(/\d{3}/);
  });

  it("renders nothing for general information", () => {
    const { container } = renderWithProviders(
      <SafetyNotice category="general_medical_information" />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});

describe("Disclaimer", () => {
  it("falls back to the default disclaimer text", () => {
    renderWithProviders(<Disclaimer />);
    expect(screen.getByText(/educational purposes only/i)).toBeInTheDocument();
  });
});

describe("ConfidenceBadge", () => {
  it("labels the value as retrieval confidence, not accuracy", () => {
    renderWithProviders(<ConfidenceBadge confidence={0.83} />);
    expect(screen.getByText(/retrieval confidence/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/retrieval confidence 83 percent/i)).toBeInTheDocument();
    expect(screen.queryByText(/accurate/i)).toBeNull();
  });

  it("renders nothing when confidence is missing", () => {
    const { container } = renderWithProviders(<ConfidenceBadge confidence={undefined} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("SourceCard", () => {
  it("displays source number, question, metadata, score, and link", () => {
    renderWithProviders(<SourceCard source={SOURCE} />);
    expect(screen.getByText("Source [1]")).toBeInTheDocument();
    expect(screen.getByText(SOURCE.question)).toBeInTheDocument();
    expect(screen.getByText("NIHSeniorHealth")).toBeInTheDocument();
    expect(screen.getByText(/87% relevance/i)).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /view source/i });
    expect(link).toHaveAttribute("href", SOURCE.source_url);
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("omits the link when no source_url is supplied", () => {
    renderWithProviders(<SourceCard source={{ ...SOURCE, source_url: undefined }} />);
    expect(screen.queryByRole("link", { name: /view source/i })).toBeNull();
  });
});

describe("ErrorMessage", () => {
  it("announces errors via role=alert", () => {
    renderWithProviders(<ErrorMessage message="Unable to connect to the MedResearch AI service." />);
    expect(screen.getByRole("alert")).toHaveTextContent(/unable to connect/i);
  });
});

describe("WelcomeScreen", () => {
  it("shows the welcome heading and sends example questions on click", () => {
    const onExample = vi.fn();
    renderWithProviders(<WelcomeScreen onExampleClick={onExample} />);
    expect(
      screen.getByRole("heading", { name: /how can i help with your medical research/i }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByText("What are the symptoms of diabetes?"));
    expect(onExample).toHaveBeenCalledWith("What are the symptoms of diabetes?");
  });
});

describe("ChatInput", () => {
  it("sends trimmed text on Enter and clears the field", () => {
    const onSend = vi.fn();
    renderWithProviders(<ChatInput onSend={onSend} disabled={false} />);
    const input = screen.getByLabelText(/ask a medical research question/i);
    fireEvent.change(input, { target: { value: "  What is asthma?  " } });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSend).toHaveBeenCalledWith("What is asthma?");
    expect((input as HTMLTextAreaElement).value).toBe("");
  });

  it("does not send empty messages", () => {
    const onSend = vi.fn();
    renderWithProviders(<ChatInput onSend={onSend} disabled={false} />);
    const input = screen.getByLabelText(/ask a medical research question/i);
    fireEvent.keyDown(input, { key: "Enter" });
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables the send button while loading", () => {
    renderWithProviders(<ChatInput onSend={() => {}} disabled={true} />);
    const input = screen.getByLabelText(/ask a medical research question/i);
    fireEvent.change(input, { target: { value: "question" } });
    expect(screen.getByRole("button", { name: /send question/i })).toBeDisabled();
  });
});
