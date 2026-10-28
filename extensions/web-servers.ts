// web-servers: registers the kit's web servers (web-mcp.json, Pi's own mcpServers format) with
// Pi's built-in MCP support for one run. scripts/pi-role loads it only into a role whose tools
// list `web` and names the list with --octo-feather-web-servers (spec roles#launch-web).
// Why an extension: Pi has no flag naming an mcp.json file, and pi.registerMcpServer is Pi's own
// way to add a server for one session. It adds no MCP client: Pi connects the servers. Exposure
// defaults to direct, so the web tools are declared to the model and callable from codemode.
import { readFileSync } from "node:fs";

// Pi's extension API, only the parts this file uses: local types, as resume-on-error.ts (#245).
interface Pi {
  registerFlag(name: string, options: { description: string; type: "string" }): void;
  getFlag(name: string): unknown;
  on(event: "session_start", handler: () => void): void;
  registerMcpServer(name: string, config: Record<string, unknown>): void;
}

// The list's shape: Pi's mcp.json, each server's config passed to Pi as it is.
interface WebList { mcpServers?: Record<string, Record<string, unknown>> }

const FLAG = "octo-feather-web-servers";

export default function (pi: Pi) {
  pi.registerFlag(FLAG, { description: "the kit's web server list (Pi mcpServers format)", type: "string" });
  pi.on("session_start", () => {
    const path = pi.getFlag(FLAG);
    if (typeof path !== "string" || !path) return;
    const servers = (JSON.parse(readFileSync(path, "utf8")) as WebList).mcpServers ?? {};
    for (const [name, config] of Object.entries(servers)) {
      pi.registerMcpServer(name, { exposure: "direct", ...config });
    }
  });
}
