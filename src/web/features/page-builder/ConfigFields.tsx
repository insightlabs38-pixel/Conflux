import { SchemaForm } from "../../components/SchemaForm";
import type { ConfigSchema } from "./configSchema";

/** A block's configuration controls: the shared schema form over the block's own schema. */
export function ConfigFields({
  schema,
  config,
  onChange,
}: {
  schema: ConfigSchema;
  config: Record<string, unknown>;
  onChange: (config: Record<string, unknown>) => void;
}) {
  return <SchemaForm schema={schema} value={config} onChange={onChange} />;
}
