import { Icon } from "./Icon";

export function DeniedState({
  message = "You do not have access to this page.",
}: {
  message?: string;
}) {
  return (
    <div className="cx-state cx-state--denied" role="alert">
      <p className="cx-state__title">
        <Icon name="lock" /> Access denied
      </p>
      <p>{message}</p>
    </div>
  );
}
