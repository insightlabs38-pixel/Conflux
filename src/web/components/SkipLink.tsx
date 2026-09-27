/** First focusable element on the page; jumps keyboard users past the header nav. */
export function SkipLink({ targetId }: { targetId: string }) {
  return (
    <a className="cx-skip-link" href={`#${targetId}`}>
      Skip to main content
    </a>
  );
}
