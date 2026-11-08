// A static real VCR recording, imported as fixture data, not a second cassette format or parser.
// Each recorded interaction is usable once; no fallback handler.
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import tape from "./recordings/uuid.json" with { type: "json" };

export { tape };

export function replayServer() {
  return setupServer(...tape.interactions.map(({ request, response }) => http.get(
    ({ request: outgoing }) => outgoing.url === request.uri,
    () => new HttpResponse(response.body.string, {
      status: response.status.code,
      statusText: response.status.message,
      headers: Object.fromEntries(Object.entries(response.headers).map(([key, values]) => [key, values.join(", ")])),
    }),
    { once: true },
  )));
}
