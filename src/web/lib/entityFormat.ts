import type { EntityField } from "./entityQuery";

/** A cell value as the lists show it: empty is a dash, yes/no for flags, dates in UTC, words for codes. */
export function showValue(field: EntityField, value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (field.type === "bool") return value ? "Yes" : "No";
  if (field.type === "date" && typeof value === "string")
    return (
      new Date(value).toLocaleString("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }) + " UTC"
    );
  return String(value).replace(/_/g, " ");
}
