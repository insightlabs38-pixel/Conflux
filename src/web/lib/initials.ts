/**
 * The letters a name is drawn as when there is no picture: the first letter or digit of each of its
 * first two words, so "(Open) Data" is OD and not "(D"; a name with no letters at all falls back to
 * its first visible character, and only an empty name is "?". The server has the same rule
 * (`presentation/showcase.py initials`); `tests/fixtures/initials_cases.json` is run by both.
 */
export function initials(name: string | null | undefined): string {
  const text = String(name ?? "");
  const found: string[] = [];
  for (const word of text.split(/\s+/)) {
    const letter = Array.from(word).find((ch) => /[\p{L}\p{N}]/u.test(ch));
    if (letter) found.push(letter);
    if (found.length === 2) break;
  }
  if (found.length === 0)
    found.push(Array.from(text).find((ch) => !/\s/u.test(ch)) ?? "?");
  return found.join("").toLocaleUpperCase();
}
