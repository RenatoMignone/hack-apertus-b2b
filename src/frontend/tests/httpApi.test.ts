import assert from 'node:assert/strict';
import test from 'node:test';
import { createHttpApi, ApiError } from '../src/api/httpApi.ts';

const hash = 'a'.repeat(64), selection = 'b'.repeat(64);
const expected = { resultId: 'result', resultHash: hash };
function detail(reviewed = true) {
  return { case: { id: 'case', companyLabel: 'Synthetic', status: 'in_review', keptCount: 1 },
    inputId: 'input', revision: 3, selectionHash: selection, currentRevisionId: 'result',
    currentRun: { run_id: 'run', input_id: 'input', status: 'queued' },
    revisions: [{ id: 'result', resultHash: hash, reasons: [{ id: 'reason', selection: reviewed ? 'kept' : 'none' }] }],
    turns: [{ id: 'turn', followUp: { id: 'question' } }], evidence: {} };
}
function harness(handler: (url: string, method: string, body: any, headers: Headers) => unknown, options = {}) {
  const calls: { url: string; method: string; body: any; headers: Headers }[] = [];
  const fetcher: typeof fetch = async (url, init) => {
    const method = init?.method ?? 'GET', headers = new Headers(init?.headers);
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ url: String(url), method, body, headers });
    assert.equal(headers.get('Authorization'), 'Bearer personal-token');
    assert.equal(init?.credentials, 'omit');
    assert.equal(init?.redirect, 'error');
    if (method !== 'GET') assert.ok(headers.get('Idempotency-Key'));
    const result = await handler(String(url), method, body, headers);
    return result instanceof Response ? result : Response.json(result);
  };
  return { calls, api: createHttpApi({ baseUrl: 'http://localhost:8000', token: () => 'personal-token',
    fetcher, pause: async () => {}, maxPolls: 4, ...options }) };
}

test('create and reconnect to a queued run; polling pauses for durable clarification', async () => {
  const { api, calls } = harness((url, method) => {
    if (method === 'POST') return { case_id: 'case', input_id: 'input', run_id: 'run' };
    if (url.endsWith('/runs/run')) return { status: 'waiting_for_input', stage: 'interpreting' };
    return detail();
  });
  await api.createCase('Permitted context');
  const stages: string[] = [];
  const value = await api.runCase('case', (stage) => stages.push(stage));
  assert.equal(value.turns[0].followUp?.id, 'question');
  assert.deepEqual(calls.filter((c) => c.method === 'POST').map((c) => c.body), [{ prompt: 'Permitted context', run: true }]);
  assert.deepEqual(stages, ['interpreting', 'done']);
});

test('clarification uses server question, input and run IDs', async () => {
  const { api, calls } = harness((url, method) => method === 'POST'
    ? { status_url: '/api/v1/cases/case/runs/run' }
    : url.endsWith('/runs/run') ? { status: 'succeeded', stage: 'done' } : detail());
  await api.answerFollowUp('case', 'turn', 'Research', () => {});
  const command = calls.find((c) => c.method === 'POST')!;
  assert.ok(command.url.endsWith('/runs/run/answers'));
  assert.deepEqual(command.body, { input_id: 'input', question_id: 'question', answer: 'Research' });
});

test('all-reviewed and visible revision hashes gate export before any writes', async () => {
  for (const reviewed of [false, true]) {
    const { api, calls } = harness(() => detail(reviewed));
    await assert.rejects(api.exportDeck('case', reviewed ? { ...expected, resultHash: 'c'.repeat(64) } : expected));
    assert.equal(calls.filter((c) => c.method !== 'GET').length, 0);
  }
});

test('review, export polling and PDF download carry exact hashes and authentication', async () => {
  const { api, calls } = harness((url) => {
    if (url.endsWith('/reviews')) return { review_id: 'review' };
    if (url.endsWith('/exports')) return { status_url: '/api/v1/operations/op' };
    if (url.endsWith('/operations/op')) return { status: 'committed', download_url: '/api/v1/cases/case/exports/pdf/download' };
    if (url.endsWith('/download')) return new Response('%PDF-1.4 synthetic', { headers: { 'Content-Type': 'application/pdf' } });
    return detail();
  });
  const result = await api.exportDeck('case', expected);
  assert.equal(result.blob.type, 'application/pdf');
  assert.equal(result.filename, 'bern-report-result.pdf');
  const review = calls.find((c) => c.url.endsWith('/reviews'))!.body;
  assert.equal(review.expected_result_hash, hash);
  assert.equal(review.expected_selection_hash, selection);
  assert.equal(calls.find((c) => c.url.endsWith('/exports'))!.body.review_id, 'review');
});

test('selection never applies a click to an unseen replacement report', async () => {
  const { api, calls } = harness(() => ({ ...detail(), currentRevisionId: 'replacement' }));
  await assert.rejects(api.setSelection('case', 'reason', 'kept', expected));
  assert.equal(calls.filter((c) => c.method === 'PUT').length, 0);
});

test('transport retry reuses its mutation idempotency key; conflicts do not retry', async () => {
  let writes = 0;
  const { api, calls } = harness((_url, method) => {
    if (method === 'PUT' && ++writes === 1) throw new TypeError('network failure');
    return detail();
  });
  await api.setSelection('case', 'reason', 'kept', expected);
  const keys = calls.filter((c) => c.method === 'PUT').map((c) => c.headers.get('Idempotency-Key'));
  assert.equal(keys.length, 2); assert.equal(keys[0], keys[1]);
  const rejected = harness((_url, method) => method === 'PUT'
    ? Response.json({ error: { code: 'stale_revision' } }, { status: 409 }) : detail());
  await assert.rejects(rejected.api.setSelection('case', 'reason', 'kept', expected), ApiError);
  assert.equal(rejected.calls.filter((c) => c.method === 'PUT').length, 1);
});

test('hold, closed outcome and action answers use persistent backend fields', async () => {
  const { api, calls } = harness((url) => url.includes('/action-items') ? [] : detail());
  await api.setCaseFlags('case', { onHold: true, outcome: 'visit' });
  await api.addActionItem('case', 'Who knows this unit?', 'Account owner');
  await api.setActionStatus('action', 'done', 'Ask the existing contact.');
  assert.deepEqual(calls.find((c) => c.method === 'PATCH' && c.url.endsWith('/case'))!.body,
    { expected_revision: 3, on_hold: true, outcome: 'visit' });
  assert.equal(calls.find((c) => c.method === 'PATCH' && c.url.endsWith('/action'))!.body.answer, 'Ask the existing contact.');
});

test('run failures stay visible and server download URLs cannot change origin', async () => {
  const failed = harness((url) => url.endsWith('/runs/run')
    ? { status: 'failed', error_code: 'evidence_rejected' } : detail());
  await assert.rejects(failed.api.runCase('case', () => {}), /failed validation/);
  const unsafe = harness((url) => url.endsWith('/reviews') ? { review_id: 'review' }
    : url.endsWith('/exports') ? { status_url: 'https://outside.invalid/steal' } : detail());
  await assert.rejects(unsafe.api.exportDeck('case', expected), /Invalid API path/);
  assert.ok(unsafe.calls.every((c) => c.url.startsWith('http://localhost:8000/')));
});
