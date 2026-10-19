import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom';
import { Theme } from '@radix-ui/themes';
import CaseWorkspace from '../../src/pages/CaseWorkspace';
import ChatPanel from '../../src/components/ChatPanel';
import { setAccessToken } from '../../src/api/session';
import { ApiError } from '../../src/api/httpApi';
import type { CaseDetail } from '../../src/types/contract';

const {api} = vi.hoisted(() => ({api: {getCase:vi.fn(), runCase:vi.fn(), sendMessage:vi.fn(),
  answerFollowUp:vi.fn(), setSelection:vi.fn(), setStatus:vi.fn()}}));
vi.mock('../../src/api', () => ({api, apiMode:'http'}));
vi.mock('../../src/components/SearchSankey', () => ({default: () => <div>Search lineage</div>}));

function deferred<T>() { let resolve!: (v:T)=>void, reject!: (e:unknown)=>void;
  const promise = new Promise<T>((yes,no) => {resolve=yes;reject=no;}); return {promise,resolve,reject}; }
function detail(id='a'): CaseDetail {
  return {case:{id,companyLabel:`Fictional ${id}`,oneLineNeed:'Synthetic testing',status:'in_review',
    createdAt:'2026-01-01',updatedAt:'2026-01-01',keptCount:0}, inputId:'input',revision:1,
    currentRevisionId:'result', selectionHash:'selection',currentRun:{run_id:'run',input_id:'input',status:'succeeded'},
    revisions:[{id:'result',createdAt:'2026-01-01',changeNote:'Fixture',changedReasonIds:[],resultHash:'hash',
      reasons:[{id:'reason',headline:'Fictional capability',category:'groups',selection:'none',
        line:{text:'Fictional test only',evidenceIds:[]},entries:[]}],openQuestions:[],
      trace:{inputs:[],terms:[],links:[]},coverage:{resultKind:'partial',snapshotDate:'2026-01-01',institutions:[],limitations:['Fixture only']}}],
    turns:[],evidence:{}};
}
function Navigation() { const go=useNavigate(); return <button onClick={()=>go('/cases/b')}>Other case</button>; }
function mount() { return render(<Theme><MemoryRouter initialEntries={['/cases/a']}><Navigation />
  <Routes><Route path="/cases/:id" element={<CaseWorkspace />} /></Routes></MemoryRouter></Theme>); }
beforeEach(() => { api.getCase.mockImplementation(async id=>detail(id)); localStorage.clear(); });

describe('workspace recovery', () => {
  it('late initial response cannot replace the case reached through navigation', async () => {
    const old = deferred<CaseDetail>();
    api.getCase.mockImplementation(id=>id==='a'?old.promise:Promise.resolve(detail('b')));
    mount(); fireEvent.click(screen.getByText('Other case'));
    await screen.findByRole('heading',{name:'Fictional b'});
    await act(async()=>old.resolve(detail('a')));
    expect(screen.queryByRole('heading',{name:'Fictional a'})).toBeNull();
  });
  it('double selection clicks produce one write; conflict refreshes without replay', async () => {
    const selection = deferred<CaseDetail>(); api.setSelection.mockReturnValue(selection.promise);
    mount(); await screen.findByRole('heading',{name:'Fictional a'});
    const keep = screen.getByRole('button',{name:'Keep',exact:true});
    fireEvent.click(keep); fireEvent.click(keep);
    expect(api.setSelection).toHaveBeenCalledTimes(1);
    const newer=detail();newer.revision=2;newer.revisions[0].reasons[0].headline='Replacement capability';
    api.getCase.mockResolvedValue(newer);
    await act(async()=>selection.reject(new ApiError(409,'stale_revision')));
    await screen.findByText('Replacement capability');
    expect(screen.getByRole('alert').textContent).toContain('latest state is loaded');
    expect(api.setSelection).toHaveBeenCalledTimes(1);
  });
  it('navigation aborts observation and ignores its late completion', async () => {
    const old=deferred<CaseDetail>(); let signal:AbortSignal|undefined;
    api.getCase.mockImplementation(async id=>{const d=detail(id);if(id==='a')d.currentRun!.status='running';return d;});
    api.runCase.mockImplementation((_id,_progress,s)=>{signal=s;return old.promise;});
    mount(); await waitFor(()=>expect(api.runCase).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByText('Other case')); await screen.findByRole('heading',{name:'Fictional b'});
    expect(signal!.aborted).toBe(true);
    await act(async()=>old.resolve(detail('a')));
    expect(screen.queryByRole('heading',{name:'Fictional a'})).toBeNull();
  });
  it('failed research preserves an existing report and offers the appropriate retry', async () => {
    const d=detail();d.currentRun={...d.currentRun!,status:'failed',pack_id:'pack',error_code:'invalid_model_output'};
    api.getCase.mockResolvedValue(d);mount();
    await screen.findByText('Fictional capability');
    expect(screen.getByRole('button',{name:'Retry report from existing evidence'})).toBeTruthy();
  });
});

it('chat retains text after a rejected submission and prevents duplicate sends', async () => {
  const pending=deferred<boolean>(); const send=vi.fn(()=>pending.promise);
  render(<ChatPanel turns={[]} running={false} stage="done" suggestions={[]} onSend={send} onAnswer={()=>{}} onClose={()=>{}} />);
  const box=screen.getByRole('textbox',{name:'Message the agent'});
  fireEvent.change(box,{target:{value:'Preserve this instruction'}});
  fireEvent.click(screen.getByRole('button',{name:'Send'}));fireEvent.click(screen.getByRole('button',{name:'Send'}));
  expect(send).toHaveBeenCalledTimes(1);
  await act(async()=>pending.resolve(false));
  expect((box as HTMLTextAreaElement).value).toBe('Preserve this instruction');
});

it('reopening a running case observes the durable run again', async () => {
  const d=detail();d.currentRun!.status='running';api.getCase.mockResolvedValue(d);
  api.runCase.mockImplementation(()=>new Promise(()=>{}));
  const first=mount();await waitFor(()=>expect(api.runCase).toHaveBeenCalledTimes(1));
  first.unmount();mount();await waitFor(()=>expect(api.runCase).toHaveBeenCalledTimes(2));
  expect(api.sendMessage).not.toHaveBeenCalled();
});

it('clarification resumes its question once while retaining the displayed report', async () => {
  const d=detail();d.currentRun!.status='waiting_for_input';d.currentRun!.questions=[{id:'q',question:'Which sensor?',status:'open'}];
  d.turns=[{id:'turn',role:'agent',text:'Which sensor?',createdAt:'2026-01-01',
    followUp:{id:'q',question:'Which sensor?',choices:[]}}];
  api.getCase.mockResolvedValue(d);const answer=deferred<CaseDetail>();api.answerFollowUp.mockReturnValue(answer.promise);
  mount();const box=await screen.findByRole('textbox',{name:'Answer: Which sensor?'});
  fireEvent.change(box,{target:{value:'Glucose'}});
  fireEvent.click(screen.getByRole('button',{name:'Submit answer'}));fireEvent.click(screen.getByRole('button',{name:'Submit answer'}));
  expect(api.answerFollowUp).toHaveBeenCalledTimes(1);
  expect(screen.getByText('Fictional capability')).toBeTruthy();
  await act(async()=>answer.resolve(detail()));
});

it('a late selection response cannot replace a different case', async () => {
  const selection=deferred<CaseDetail>();api.setSelection.mockReturnValue(selection.promise);
  mount();await screen.findByRole('heading',{name:'Fictional a'});
  fireEvent.click(screen.getByRole('button',{name:'Keep',exact:true}));
  fireEvent.click(screen.getByText('Other case'));await screen.findByRole('heading',{name:'Fictional b'});
  await act(async()=>selection.resolve(detail('a')));
  expect(screen.queryByRole('heading',{name:'Fictional a'})).toBeNull();
});

it('closing and reopening chat retains unsent instructions in memory',async()=>{
  mount();const box=await screen.findByRole('textbox',{name:'Message the agent'});
  fireEvent.change(box,{target:{value:'Do not lose my text'}});
  fireEvent.click(screen.getByRole('button',{name:'Close chat'}));
  fireEvent.click(screen.getByRole('button',{name:'Chat with the agent'}));
  expect((screen.getByRole('textbox',{name:'Message the agent'}) as HTMLTextAreaElement).value).toBe('Do not lose my text');
});

it('a failed model step keeps the prior report and the submitted instruction',async()=>{
  mount();const box=await screen.findByRole('textbox',{name:'Message the agent'});
  const failed=detail();failed.currentRun={...failed.currentRun!,status:'failed',pack_id:'pack',error_code:'invalid_model_output'};
  api.getCase.mockResolvedValue(failed);api.sendMessage.mockRejectedValue(new ApiError(502,'invalid_model_output'));
  fireEvent.change(box,{target:{value:'Keep the caveats while rewriting'}});
  await act(async()=>fireEvent.click(screen.getByRole('button',{name:'Send'})));
  expect(screen.getByText('Fictional capability')).toBeTruthy();
  expect((screen.getByRole('textbox',{name:'Message the agent'}) as HTMLTextAreaElement).value).toBe('Keep the caveats while rewriting');
  expect(screen.getByRole('button',{name:'Retry report from existing evidence'})).toBeTruthy();
});

it('valid no-match is an outcome, not a backend failure or a retry command',async()=>{
  const d=detail();d.revisions[0].reasons=[];d.revisions[0].coverage.resultKind='no_match';
  d.revisions[0].emptyMessage='No supported expertise in this fictional corpus.';api.getCase.mockResolvedValue(d);
  mount();await screen.findByText('No reliable match');
  expect(screen.queryByRole('alert')).toBeNull();expect(screen.queryByRole('button',{name:'Retry research'})).toBeNull();
});


it('session reconnect during observation cannot cancel the replacement case load',async()=>{
  const running=detail();running.currentRun!.status='running';api.getCase.mockResolvedValue(running);
  const old=deferred<CaseDetail>(), next=deferred<CaseDetail>();
  api.runCase.mockReturnValueOnce(old.promise).mockReturnValueOnce(next.promise);
  mount();await waitFor(()=>expect(api.runCase).toHaveBeenCalledTimes(1));
  act(()=>setAccessToken('reconnected-synthetic'));
  await waitFor(()=>expect(api.runCase).toHaveBeenCalledTimes(2));
  await act(async()=>next.resolve(detail()));
  expect(screen.getByText('Fictional capability')).toBeTruthy();
  await act(async()=>old.resolve(detail('old')));
  expect(screen.queryByRole('heading',{name:'Fictional old'})).toBeNull();
});
