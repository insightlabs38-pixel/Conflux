/**
 * Page-block configuration schemas. The validator, defaults and sentences are the platform's
 * shared schema subset (`lib/schema.ts`, PD-F002-B02-T01); these names are what the page builder
 * has always imported.
 */
import { defaults, firstError, type Schema } from "../../lib/schema";

export type ConfigSchema = Schema;

export function configDefaults(
  schema: ConfigSchema,
  creating = false,
): Record<string, unknown> {
  return defaults(schema, creating);
}

export function configError(schema: ConfigSchema, value: unknown): string {
  return firstError(schema, value);
}
