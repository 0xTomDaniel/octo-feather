# When to Mock

Mock only systems the repo does not control, each at an explicit **system boundary** (a seam):

- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)

Don't mock:

- Your own classes/modules
- Internal collaborators
- Anything you control

A stand-in returns what the real system would and nothing more: the app's own validation and business logic run in the app, never in the stand-in.

## Recordings

A recording is a tape, never a simulator. Replay each recorded response unmodified, its status, headers and body byte for byte: no fallback response, no synthesized error (an error case replays a recorded real error). A missing fixture or recording fails loudly, with an error naming what is missing. No recording yet: record one from the real system, or stop and ask the user; never invent the response.

## Test support

Shared test support (stand-ins, fixtures, recordings, helpers) lives in one place, the repo's testkit, not in helpers scattered beside the tests.

## Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

**1. Use dependency injection**

Pass external dependencies in rather than creating them internally:

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. Prefer SDK-style interfaces over generic fetchers**

Create specific functions for each external operation instead of one generic function with conditional logic:

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

The SDK approach means:
- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint
