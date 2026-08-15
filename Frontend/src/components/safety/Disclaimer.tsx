interface DisclaimerProps {
  text?: string | null;
}

const DEFAULT_TEXT =
  "This information is for educational purposes only and is not a diagnosis or a substitute for professional medical advice.";

export function Disclaimer({ text }: DisclaimerProps) {
  return (
    <p className="mt-3 border-t border-border pt-2.5 text-xs italic leading-relaxed text-muted-foreground">
      {text || DEFAULT_TEXT}
    </p>
  );
}
