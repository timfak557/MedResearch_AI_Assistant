import { Fragment, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Citation } from "./Citation";

interface AnswerMarkdownProps {
  markdown: string;
  onCitationClick: (id: number) => void;
}

const CITATION_RE = /\[(\d{1,3}(?:\s*,\s*\d{1,3})*)\]/g;

/** Replace [1] / [1, 2] markers inside a text node with Citation buttons. */
function withCitations(text: string, onClick: (id: number) => void): ReactNode {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let key = 0;
  for (const match of text.matchAll(CITATION_RE)) {
    const index = match.index ?? 0;
    if (index > lastIndex) parts.push(text.slice(lastIndex, index));
    const idList = match[1] ?? "";
    for (const raw of idList.split(",")) {
      const id = Number.parseInt(raw.trim(), 10);
      if (Number.isFinite(id)) parts.push(<Citation key={`c${key++}`} id={id} onClick={onClick} />);
    }
    lastIndex = index + match[0].length;
  }
  if (parts.length === 0) return text;
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return <Fragment>{parts}</Fragment>;
}

function transformChildren(children: ReactNode, onClick: (id: number) => void): ReactNode {
  if (typeof children === "string") return withCitations(children, onClick);
  if (Array.isArray(children)) {
    return children.map((child, index) =>
      typeof child === "string" ? (
        <Fragment key={index}>{withCitations(child, onClick)}</Fragment>
      ) : (
        child
      ),
    );
  }
  return children;
}

/** Sanitized markdown renderer (react-markdown never injects raw HTML) with
 * interactive citations woven into every text node. */
export function AnswerMarkdown({ markdown, onCitationClick }: AnswerMarkdownProps) {
  return (
    <div className="prose-answer">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        components={{
          p: ({ children }) => <p>{transformChildren(children, onCitationClick)}</p>,
          li: ({ children }) => <li>{transformChildren(children, onCitationClick)}</li>,
          td: ({ children }) => <td>{transformChildren(children, onCitationClick)}</td>,
          strong: ({ children }) => <strong>{transformChildren(children, onCitationClick)}</strong>,
          em: ({ children }) => <em>{transformChildren(children, onCitationClick)}</em>,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
