import { afterEach, describe, expect, it, vi } from "vitest";
import { replayServer, tape } from "./testkit/replay.ts";

const server = replayServer();
afterEach(() => {
  server.close();
  vi.restoreAllMocks();
});

describe("strict replay", () => {
  it("replays the recording once then rejects the exhausted URL", async () => {
    server.listen({ onUnhandledRequest: "error" });
    const recorded = tape.interactions[0];
    expect(recorded).toBeDefined();
    if (!recorded) throw new Error("Missing recorded interaction");
    const response = await fetch(recorded.request.uri);
    expect(response.status).toBe(recorded.response.status.code);
    expect(Buffer.from(await response.arrayBuffer())).toEqual(Buffer.from(recorded.response.body.string));
    const diagnostic = vi.spyOn(console, "error").mockImplementation(() => undefined);
    await expect(fetch(recorded.request.uri)).rejects.toThrow();
    expect(diagnostic.mock.calls.flat().join("\n")).toContain(recorded.request.uri);
  });

  it("rejects a missing recording with the actual URL in its diagnostic", async () => {
    server.listen({ onUnhandledRequest: "error" });
    const diagnostic = vi.spyOn(console, "error").mockImplementation(() => undefined);
    for (const missing of [
      "https://httpbin.org/uuid/unrecorded?request=missing",
      "https://httpbin.org/uuid?request=missing",
    ]) {
      diagnostic.mockClear();
      await expect(fetch(missing)).rejects.toThrow();
      expect(diagnostic.mock.calls.flat().join("\n")).toContain(missing);
    }
  });
});
