// web-servers: registers the kit's web servers (web-mcp.json, Pi's own mcpServers format) with
// Pi's built-in MCP support for one run. scripts/pi-role loads it only into a role whose tools
// list `web` and names the list with --octo-feather-web-servers (spec roles#launch-web).
// Why an extension: Pi has no flag naming an mcp.json file, and pi.registerMcpServer is Pi's own
// way to add a server for one session. It adds no MCP client: Pi connects the servers. Exposure
// defaults to direct, so the web tools are declared to the model and callable from codemode.
import { readFileSync } from "node:fs";

const FLAG = "octo-feather-web-servers";

export default function (pi: any) {
  pi.registerFlag(FLAG, { description: "the kit's web server list (Pi mcpServers format)", type: "string" });
  pi.on("session_start", async () => {
    const path = pi.getFlag(FLAG);
    if (typeof path !== "string" || !path) return;
    const servers = JSON.parse(readFileSync(path, "utf8")).mcpServers ?? {};
    for (const [name, config] of Object.entries(servers)) {
      pi.registerMcpServer(name, { exposure: "direct", ...(config as object) });
    }
  });
}
