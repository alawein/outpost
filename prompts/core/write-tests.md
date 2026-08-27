---
name: write-tests
description: Use when adding coverage for new or uncovered code. Generates tests that assert the behavior and the contract, not implementation detail, and that actually run.
---

# write-tests

Use this when you need coverage for new or uncovered behavior. Write tests that verify what the code
promises, not how it happens to work. Add unit tests for the touched behavior and an integration
test for at least one consumer.

## When to use it

- New code, or working code that lacks coverage for a behavior that matters.
- Not for diagnosing a failure; that is debug-failure.

## Required inputs

- The code under test and its intended contract: inputs, outputs, invariants, error cases.
- The test command, and the ability to run it.

## Steps

1. Name the contract: inputs, outputs, invariants, error cases, and the path where the code refuses or returns nothing.
2. Cover three groups: the normal path, the edges, and the failure modes.
3. Add unit tests for the touched behavior and an integration test for at least one consumer. A change on a public entry point (an API route, a CLI command, an exported function) adds an integration test through that entry point on top of the unit test.
4. Keep tests isolated: no network, no real device, and no shared state. If isolation is hard, say so, add the next-best coverage, and record the gap.
5. Run the suite and confirm the new tests pass. Do not narrow the suite only to get green.

## Output format

- Test diff: the new or changed tests.
- Test list: a line per test naming the group and the contract it pins.
- Command result: the command run and its result.

## Stop conditions

- Stop when the three groups are covered and the suite passes.
- Do not assert on prompt text or pure delegation; test what the contract promises.
- A test that cannot fail is not a test. Drop it or fix it.
