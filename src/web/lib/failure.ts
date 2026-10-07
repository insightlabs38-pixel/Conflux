import { ApiError } from "./api";

/**
 * What a failure means for the person's data, said only as far as it is known (S-ERR).
 * - A failed read never changes anything.
 * - A write the server answered with a refusal (4xx) was not applied: the domain services validate
 *   before they write.
 * - A write that failed without a refusal (a server error, a dropped connection, a timeout) may or
 *   may not have been applied, and the message says exactly that instead of reassuring.
 * Retrying is never automatic for a write; the note says what the button will do.
 */
export type FailureKind = "read" | "write";
export type Failure = { kept: string; retry: string };

export function describeFailure(error: unknown, kind: FailureKind): Failure {
  if (kind === "read")
    return {
      kept: "Nothing was changed.",
      retry: "Try again loads it again.",
    };
  if (error instanceof ApiError && error.status >= 400 && error.status < 500)
    return {
      kept: "The server refused the change, so nothing was saved.",
      retry:
        "Try again sends the same change; fix what the message says first or it will be refused again.",
    };
  return {
    kept: "We could not confirm whether the change was saved. Check before repeating it.",
    retry: "Try again sends the same change again.",
  };
}
