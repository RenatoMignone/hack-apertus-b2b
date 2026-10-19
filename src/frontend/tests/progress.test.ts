import assert from 'node:assert/strict';
import test from 'node:test';
import { beginCase, pendingCase, forgetPendingCase } from '../src/api/pendingCase.ts';
import { nextPollDelay } from '../src/api/progress.ts';
import { createHttpApi } from '../src/api/httpApi.ts';

test('case preparation routes immediately while the create request is pending', async () => {
  let finish!: (value: any) => void;
  let calls = 0;
  const id = beginCase('Synthetic public prompt', async () => { calls++; return new Promise((resolve) => { finish=resolve; }); });
  assert.ok(pendingCase(id));
  await Promise.resolve();
  assert.equal(calls,1);
  finish({case:{id:'saved'}});
  assert.equal((await pendingCase(id)!.promise).case.id,'saved');
  forgetPendingCase(id);
  assert.equal(pendingCase(id),undefined);
});

test('unchanged polling backs off and resets with progress', () => {
  assert.equal(nextPollDelay(1200,0),1200);
  assert.equal(nextPollDelay(1200,3),3000);
  assert.equal(nextPollDelay(1200,100),5000);
});

test('local access requests omit tokens and concurrent detail reads are coalesced', async () => {
  let calls=0;
  const api=createHttpApi({token:()=>'',fetcher:async (_url, init) => {
    calls++;
    assert.equal((init!.headers as Record<string,string>).Authorization,undefined);
    return new Response(JSON.stringify({case:{id:'saved'}}),{status:200});
  }});
  const [a,b]=await Promise.all([api.getCase('saved'),api.getCase('saved')]);
  assert.equal(calls,1);
  assert.deepEqual(a,b);
});

test('leaving a case stops observation without cancelling backend work', async () => {
  const controller=new AbortController();
  const writes:string[]=[];
  const api=createHttpApi({token:()=>'',pause:async()=>{controller.abort();},fetcher:async (url,init)=>{
    if(init!.method!=='GET')writes.push(String(url));
    return new Response(JSON.stringify(String(url).endsWith('/runs/r') ? {status:'running',stage:'searching'} :
      {case:{id:'c'},revision:1,inputId:'i',revisions:[],currentRun:{run_id:'r',status:'running'}}),{status:200});
  }});
  await assert.rejects(api.runCase('c',()=>{},controller.signal),{name:'AbortError'});
  assert.deepEqual(writes,[]);
});
