// relay.json, the service's settings: read and validated once here; the rest of the code trusts a Settings.
import { readFileSync } from 'node:fs';
import { z } from 'zod';

const Settings = z.strictObject({
  endpoint: z.url(),
  retries: z.int().min(0).max(10),
});
export type Settings = z.infer<typeof Settings>;

export function readSettings(path: string): Settings {
  return Settings.parse(JSON.parse(readFileSync(path, 'utf8')));
}
