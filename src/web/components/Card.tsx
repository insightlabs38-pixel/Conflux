import type { ReactNode } from "react";

export function Card({
  title,
  children,
  as: Heading = "h3",
}: {
  title?: string;
  children: ReactNode;
  as?: "h2" | "h3" | "h4";
}) {
  return (
    <div className="cx-card">
      {title && <Heading className="cx-card__title">{title}</Heading>}
      {children}
    </div>
  );
}
