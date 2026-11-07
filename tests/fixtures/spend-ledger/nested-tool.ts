// Test fixture for tests/gate/kit/spend_ledger.py: a tool that reports nested model work, as Pi's tool
// contract asks a tool that makes model calls to do (docs/extensions.md, Tools: "include their
// usage in the result"). Its usage is literal: 7 tokens in, 3 out, $0.004.
export default function (pi: any) {
  pi.registerTool({
    name: "nested_work",
    label: "Nested work",
    description: "Does nested model work.",
    parameters: { type: "object", properties: {} },
    async execute() {
      return {
        content: [{ type: "text", text: "nested-done" }],
        details: undefined,
        usage: {
          input: 7, output: 3, cacheRead: 0, cacheWrite: 0, totalTokens: 10,
          cost: { input: 0.001, output: 0.003, cacheRead: 0, cacheWrite: 0, total: 0.004 },
        },
      };
    },
  });
}
