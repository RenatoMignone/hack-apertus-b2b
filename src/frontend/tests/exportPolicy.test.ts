import assert from 'node:assert/strict';
import test from 'node:test';
import type { BriefRevision } from '../src/types/contract.ts';
import { assertExportAllowed } from '../src/export/policy.ts';

const revision = (selections: string[], resultHash?: string) => ({
  reasons: selections.map((selection) => ({ selection })), resultHash,
}) as BriefRevision;

test('export requires all reviewed and at least one kept in both modes', () => {
  for (const mode of ['mock', 'http'] as const) {
    for (const choices of [[], ['rejected'], ['kept', 'none']]) {
      assert.throws(() => assertExportAllowed(revision(choices, 'hash'), mode, 'pdf'));
    }
  }
});

test('HTTP export requires a result hash and refuses browser PowerPoint', () => {
  assert.throws(() => assertExportAllowed(revision(['kept']), 'http', 'pdf'));
  assert.throws(() => assertExportAllowed(revision(['kept'], 'hash'), 'http', 'pptx'));
  assert.doesNotThrow(() => assertExportAllowed(revision(['kept', 'rejected'], 'hash'), 'http', 'pdf'));
});

test('reviewed demo selections support local PDF and PowerPoint', () => {
  for (const format of ['pdf', 'pptx'] as const) {
    assert.doesNotThrow(() => assertExportAllowed(revision(['kept', 'rejected']), 'mock', format));
  }
});
