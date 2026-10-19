import { expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import { useLive } from '../../src/api/useLive';
const {subscribe}=vi.hoisted(()=>({subscribe:vi.fn()}));
vi.mock('../../src/api',()=>({api:{subscribe}}));
it('an earlier list response cannot overwrite a newer reload',async()=>{
  let refresh!:()=>void, first!:(v:string)=>void;
  subscribe.mockImplementation(fn=>{refresh=fn;return ()=>{};});
  const load=vi.fn().mockImplementationOnce(()=>new Promise(resolve=>{first=resolve;})).mockResolvedValue('new');
  function List(){const value=useLive(load);return <p>{value??'loading'}</p>;}
  render(<List/>);await act(async()=>refresh());expect(screen.getByText('new')).toBeTruthy();
  await act(async()=>first('old'));expect(screen.queryByText('old')).toBeNull();
});
