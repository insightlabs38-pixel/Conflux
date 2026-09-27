export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <p className="cx-state" role="status">
      {label}
    </p>
  );
}
