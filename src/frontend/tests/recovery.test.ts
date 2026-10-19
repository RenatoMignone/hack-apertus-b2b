import assert from 'node:assert/strict';
import test from 'node:test';
import { canReusePack, failureMessage, isStateConflict } from '../src/api/recovery.ts';

test('retry label and command share current input and failed-run requirements', () => {
  const detail = {inputId: 'now', currentRun: {run_id:'r', input_id:'now', status:'failed', pack_id:'p'}} as const;
  assert.equal(canReusePack(detail), true);
  assert.equal(canReusePack({...detail, inputId:'new'}), false);
  assert.equal(canReusePack({...detail, currentRun:{...detail.currentRun, status:'running'}}), false);
  assert.equal(canReusePack({...detail, currentRun:undefined}), false);
});

test('failure messages survive reload without disclosing provider details', () => {
  assert.match(failureMessage('invalid_model_output'), /failed step/);
  assert.match(failureMessage('evidence_rejected'), /No unsupported report/);
  assert.match(failureMessage('unknown'), /could not be completed/);
});


test('model rejection is not mistaken for a stale edit conflict', () => {
  assert.equal(isStateConflict({status:409,code:'invalid_model_output'}), false);
  assert.equal(isStateConflict({status:409,code:'stale_revision'}), true);
  assert.equal(isStateConflict({status:409,code:'conflict'}), true);
  assert.equal(isStateConflict({status:503,code:'service_unavailable'}), false);
});
