import { parseArgs } from 'node:util';
import { readSettings } from './settings.ts';

const { values } = parseArgs({ options: { config: { type: 'string', default: 'relay.json' } } });
const settings = readSettings(values.config);
process.stdout.write(`relay: forwarding to ${settings.endpoint} (${settings.retries} retries)\n`);
