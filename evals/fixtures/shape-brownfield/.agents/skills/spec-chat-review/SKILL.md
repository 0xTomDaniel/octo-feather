---
name: spec-chat-review
description: Answer questions on a Spec Chat HTML spec and make atomic corrections to it (a typo, a wrong value, a broken anchor). Anything that changes behavior is spec-chat-shape's.
---

# Spec Chat Review

(A stand-in of Spec Chat's skill for the octo-feather kit's evals.)

1. Read the spec the question or correction names, and the ADRs it cites.
2. A question: answer it from the spec's text, citing the anchor.
3. An atomic correction: edit only that text, keep every anchor, and commit it on the current branch with a one-line message.
