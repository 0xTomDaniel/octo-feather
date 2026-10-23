import { createServer } from "node:http";
import { loadEnv } from "./config.ts";
import { greet } from "./core.ts";

loadEnv();
const port = 3000;

createServer((req, res) => {
  const url = new URL(req.url ?? "/", "http://localhost");
  if (url.pathname !== "/hello") {
    res.writeHead(404).end();
    return;
  }
  try {
    res.writeHead(200, { "content-type": "application/json" }).end(JSON.stringify(greet(url.searchParams.get("name") ?? "")));
  } catch (err) {
    res.writeHead(400, { "content-type": "application/json" }).end(JSON.stringify({ error: (err as Error).message }));
  }
}).listen(port, () => console.log(`listening on ${port}`));
