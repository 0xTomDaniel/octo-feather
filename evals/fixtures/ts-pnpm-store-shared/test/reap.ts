// Fixture children die with the test process that spawned them: this process's exit (a normal end, a failure, a test
// runner timeout) and SIGINT/SIGTERM send them SIGTERM.
import type { ChildProcess } from 'node:child_process';

const live = new Set<ChildProcess>();
/** Registers a fixture child to be sent SIGTERM when this test process exits or is interrupted. */
export function reaped<C extends ChildProcess>(child: C): C {
  live.add(child); child.once('exit', () => live.delete(child));
  return child;
}
process.once('exit', () => { for (const child of live) child.kill('SIGTERM'); });
for (const signal of ['SIGINT', 'SIGTERM'] as const)
  process.once(signal, () => { for (const child of live) child.kill('SIGTERM'); process.exit(signal === 'SIGINT' ? 130 : 143); });
