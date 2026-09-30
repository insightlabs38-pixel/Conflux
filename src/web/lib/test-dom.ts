import { act } from "react";

/** Flush effects and pending requests until `check()` holds (real timers, act-wrapped). */
export async function until(check: () => boolean, what = "UI update") {
  for (let attempt = 0; attempt < 200; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error(`Timed out waiting for ${what}`);
}
