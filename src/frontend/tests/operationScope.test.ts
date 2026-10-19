import assert from 'node:assert/strict';
import test from 'node:test';
import { OperationScope } from '../src/api/operationScope.ts';

test('navigation A -> B -> A cannot revive a response from the first visit', () => {
  const scope = new OperationScope('a'), first = scope.begin();
  scope.reset('b'); scope.reset('a');
  assert.equal(first.current(), false);
  assert.equal(first.signal.aborted, true);
  const second = scope.begin();
  assert.equal(second.current(), true);
  scope.stop(); assert.equal(second.current(), false);
});

test('a new operation invalidates older completions and progress callbacks', () => {
  const scope = new OperationScope('case'), old = scope.begin(), next = scope.begin();
  assert.equal(old.current(),false); assert.equal(next.current(),true);
});
