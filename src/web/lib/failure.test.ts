import { expect, it } from "vitest";
import { ApiError } from "./api";
import { describeFailure } from "./failure";

it("says a failed read changed nothing and what retry does", () => {
  const failure = describeFailure(new Error("down"), "read");
  expect(failure.kept).toBe("Nothing was changed.");
  expect(failure.retry).toContain("loads it again");
});

it("says a refused write was not saved and that retrying needs a fix first", () => {
  for (const status of [400, 403, 404, 409, 422]) {
    const failure = describeFailure(new ApiError(status, "No."), "write");
    expect(failure.kept, String(status)).toContain("nothing was saved");
    expect(failure.retry).toContain("fix what the message says");
  }
});

it("does not reassure about a write that failed without a refusal", () => {
  for (const error of [
    new ApiError(500, "Server error."),
    new ApiError(503, "Unavailable."),
    new TypeError("Failed to fetch"),
    "boom",
  ]) {
    const failure = describeFailure(error, "write");
    expect(failure.kept).toContain(
      "could not confirm whether the change was saved",
    );
    expect(failure.kept).not.toContain("nothing was saved");
    expect(failure.retry).toContain("sends the same change again");
  }
});
