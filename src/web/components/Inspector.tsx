import { useEffect, useId, useRef, type ReactNode } from "react";
import { Icon } from "./Icon";

/**
 * A panel beside a list that shows one record in detail without leaving the list (the design's
 * right inspector). The list stays where it is - it is not remounted, so its scroll position, page
 * and selection survive - and the record being shown is marked in it. From 1024px it is docked
 * beside the list; below that it is a full-height sheet over it (design D-009). It is a
 * complementary region: focus moves to its title when it opens, Escape closes it and focus goes
 * back to the control that opened it.
 */
export function Inspector({
  title,
  position,
  onClose,
  onPrevious,
  onNext,
  children,
}: {
  title: string;
  /** For example "3 of 25", said beside the Previous and Next controls. */
  position?: string;
  onClose: () => void;
  onPrevious?: () => void;
  onNext?: () => void;
  children: ReactNode;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  const titleId = useId();
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    // arriving: put the reader on the title, once
    heading.current?.focus({ preventScroll: true });
  }, []);
  return (
    <>
      <button
        type="button"
        className="cx-inspector__scrim"
        tabIndex={-1}
        aria-label="Close details"
        onClick={onClose}
      />
      <aside
        className="cx-inspector"
        aria-labelledby={titleId}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.stopPropagation();
            closeRef.current();
          }
        }}
      >
        <div className="cx-inspector__head">
          <h3
            id={titleId}
            ref={heading}
            tabIndex={-1}
            className="cx-inspector__title"
          >
            {title}
          </h3>
          <button
            type="button"
            className="cx-inspector__close"
            aria-label="Close details"
            onClick={onClose}
          >
            <Icon name="x" />
          </button>
        </div>
        {(onPrevious || onNext) && (
          <div className="cx-inspector__step">
            <button type="button" disabled={!onPrevious} onClick={onPrevious}>
              Previous
            </button>
            {position && <span role="status">{position}</span>}
            <button type="button" disabled={!onNext} onClick={onNext}>
              Next
            </button>
          </div>
        )}
        <div className="cx-inspector__body">{children}</div>
      </aside>
    </>
  );
}
