import type { ButtonHTMLAttributes } from "react";

/**
 * One primary action per local context (a form, dialog, panel or list row); everything else is
 * secondary or ghost. `danger` is the final confirm of a destructive step only: the control that
 * opens that step stays secondary, so a page is never covered in alarm colour (S-DEST).
 * Primary is never the default: a caller opts in.
 */
export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

export function buttonClass(
  variant: ButtonVariant = "secondary",
  size: ButtonSize = "md",
  extra?: string,
) {
  return [
    "cx-button",
    `cx-button--${variant}`,
    size === "md" ? "" : `cx-button--${size}`,
    extra,
  ]
    .filter(Boolean)
    .join(" ");
}

export function Button({
  variant = "secondary",
  size = "md",
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
}) {
  return (
    <button
      type="button"
      className={buttonClass(variant, size, className)}
      {...rest}
    />
  );
}
