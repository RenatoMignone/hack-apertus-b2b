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

test('failed drafting reuses its owned frozen pack instead of repeating retrieval', async () => {
  const failed = { ...detail(), currentRun: { run_id: 'failed', input_id: 'input', status: 'failed', pack_id: 'pack' } };
  const { api, calls } = harness((url, method) => method === 'POST'
    ? { status_url: '/api/v1/cases/case/runs/retry' }
    : url.endsWith('/runs/retry') ? { status: 'succeeded', stage: 'done' } : failed);
  await api.runCase('case', () => {});
  const command = calls.find((call) => call.method === 'POST')!;
  assert.ok(command.url.endsWith('/reports'));
  assert.equal(command.body.pack_id, 'pack');
  assert.equal(command.body.expected_revision, 3);
  assert.ok(!calls.some((call) => call.method === 'POST' && call.url.endsWith('/runs')));
});

test('research failures without a current-input pack start a new research run', async () => {
  const failed = { ...detail(), currentRun: { run_id: 'failed', input_id: 'older-input', status: 'failed', pack_id: 'old-pack' } };
  const { api, calls } = harness((url, method) => method === 'POST'
    ? { status_url: '/api/v1/cases/case/runs/retry' }
    : url.endsWith('/runs/retry') ? { status: 'succeeded' } : failed);
  await api.runCase('case', () => {});
  assert.ok(calls.find((call) => call.method === 'POST')!.url.endsWith('/runs'));
});

test('formatting is explicit and unanswered clarification cannot become a new focus request', async () => {
  const { api, calls } = harness((url, method) => method === 'POST'
    ? { status_url: '/api/v1/cases/case/runs/run' }
    : url.endsWith('/runs/run') ? { status: 'succeeded' } : detail());
  await api.sendMessage('case', 'Make it shorter', () => {}, 'formatting');
  assert.equal(calls.find((call) => call.method === 'POST')!.body.kind, 'formatting');
  const waiting = harness(() => ({ ...detail(), currentRun: { run_id: 'run', input_id: 'input', status: 'waiting_for_input' } }));
  await assert.rejects(waiting.api.sendMessage('case', 'My answer', () => {}), /Answer the clarification/);
  assert.equal(waiting.calls.filter((call) => call.method === 'POST').length, 0);
});

test('case history requires current reviewed hash and explicit attestations', async () => {
  const { api, calls } = harness((url) => url.endsWith('/reviews') ? {review_id:'review'} :
    {...detail(), memory:{available:true,eligible:false}});
  await api.setCaseMemory!('case', true, expected);
  const command = calls.find((c) => c.url.endsWith('/memory'))!.body;
  assert.deepEqual(command, {eligible:true,expected_revision:3,expected_result_hash:hash,
    synthetic:false,permitted_context_confirmed:true});
  await api.setCaseMemory!('case', false);
  assert.equal(calls.filter((c) => c.url.endsWith('/reviews')).length, 1);
  const denied = harness(() => ({...detail(false),memory:{available:true,eligible:false}}));
  await assert.rejects(denied.api.setCaseMemory!('case',true,expected));
  assert.equal(denied.calls.filter((c) => c.method !== 'GET').length,0);
});

test('manual business update sends exact operator values and polls replacement run', async () => {
  const { api, calls } = harness((url, method) => method === 'PUT' ? {status_url:'/api/v1/cases/case/runs/new'} :
    url.endsWith('/runs/new') ? {status:'succeeded',stage:'done'} : {...detail(),businessContextAvailable:true});
  const values = {planned_jobs:5,investment_amount:'100.00',investment_currency:'CHF',timeline:'2027, tentative'};
  await api.setBusinessContext!('case',values,()=>{},3);
  assert.deepEqual(calls.find((c) => c.method === 'PUT')!.body,
    {expected_revision:3,values,permitted_context_confirmed:true});
});

test('advertised PPTX uses authenticated exact review and PPTX download', async () => {
  const mime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
  const { api, calls } = harness((url) => {
    if (url.endsWith('/reviews')) return {review_id:'review'};
    if (url.endsWith('/exports')) return {status_url:'/api/v1/operations/op'};
    if (url.endsWith('/operations/op')) return {status:'committed',download_url:'/api/v1/cases/case/exports/pptx/download'};
    if (url.endsWith('/download')) return new Response('synthetic ZIP', {headers:{'Content-Type':mime}});
    return {...detail(),exportFormats:['pdf','pptx']};
  });
  const result = await api.exportDeck('case',expected,'pptx');
  assert.equal(result.filename,'bern-report-result.pptx');
  assert.equal(result.blob.type,mime);
  assert.equal(calls.find((c) => c.url.endsWith('/exports'))!.body.format,'pptx');
  const disabled = harness(() => detail());
  await assert.rejects(disabled.api.exportDeck('case',expected,'pptx'));
  assert.equal(disabled.calls.filter((c) => c.method !== 'GET').length,0);
});


test('manual plans cannot overwrite an unseen input revision', async () => {
  const {api,calls} = harness(() => ({...detail(),businessContextAvailable:true,revision:4}));
  await assert.rejects(api.setBusinessContext!('case',{planned_jobs:5},()=>{},3),ApiError);
  assert.equal(calls.filter((c) => c.method !== 'GET').length,0);
});


test('interrupted status observation resumes existing run without writes', async () => {
  let reads = 0;
  const { api, calls } = harness((url) => {
    if (url.endsWith('/runs/run')) {
      if (++reads <= 2) throw new TypeError('offline');
      return { status: 'succeeded', stage: 'done' };
    }
    return detail();
  });
  await api.runCase('case', () => {});
  assert.equal(reads, 3);
  assert.equal(calls.filter(c => c.method !== 'GET').length, 0);
});

test('authentication stops observation immediately; unavailable reads have a bound', async () => {
  for (const status of [401, 503]) {
    let reads = 0;
    const { api } = harness(url => {
      if (url.endsWith('/runs/run')) { reads++; return Response.json({error:{code:'service_unavailable'}}, {status}); }
      return detail();
    });
    await assert.rejects(api.runCase('case', () => {}), ApiError);
    assert.equal(reads, status === 401 ? 1 : 4);
  }
});
