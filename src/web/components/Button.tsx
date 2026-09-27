import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

export function Button({
  variant = "primary",
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const classes = ["cx-button", `cx-button--${variant}`, className]
    .filter(Boolean)
    .join(" ");
  return <button type="button" className={classes} {...rest} />;
}
