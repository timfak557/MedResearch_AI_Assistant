import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Variant = "default" | "secondary" | "outline" | "warning" | "destructive" | "success";

const variants: Record<Variant, string> = {
  default: "bg-accent text-accent-foreground",
  secondary: "bg-muted text-muted-foreground",
  outline: "border border-border text-muted-foreground",
  warning: "bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]",
  destructive: "bg-[hsl(var(--destructive)/0.1)] text-destructive",
  success: "bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium",
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
