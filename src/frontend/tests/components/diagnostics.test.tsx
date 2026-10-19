import { expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { Theme } from '@radix-ui/themes';
import ApiErrors, {reportApiError} from '../../src/components/ApiErrors';
import ConnectionGate from '../../src/components/ConnectionGate';
import { ApiError } from '../../src/api/httpApi';
import { authenticationRequired, rejectAccess, setAccessToken } from '../../src/api/session';
vi.mock('../../src/api',()=>({apiMode:'http',apiBaseUrl:''}));

it('diagnostics show and copy only the safe request ID',async()=>{
  const writeText=vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText}});
  render(<ApiErrors/>);
  act(()=>reportApiError(new ApiError(503,'storage_unavailable',{requestId:'safe-id_123',retryable:true})));
  expect(screen.getByRole('alert').textContent).toContain('safe-id_123');
  await act(async()=>fireEvent.click(screen.getByRole('button',{name:'Copy request ID'})));
  expect(writeText).toHaveBeenCalledWith('safe-id_123');
  expect(screen.getByRole('button',{name:'Copied request ID'})).toBeTruthy();
});

it('rejected authentication pauses access without unmounting unsent workspace input',async()=>{
  setAccessToken('existing');
  const fetcher=vi.fn().mockResolvedValue(Response.json({schema_version:'1',frontend_transport:'polling',formats:['pdf']}));
  vi.stubGlobal('fetch',fetcher);
  render(<Theme><ConnectionGate><label>Unsent<input aria-label="Unsent" defaultValue="Keep this text"/></label></ConnectionGate></Theme>);
  const input=await screen.findByRole('textbox',{name:'Unsent'});
  act(()=>rejectAccess());
  const dialog=screen.getByRole('dialog',{name:'Reconnect workspace'});
  expect((input as HTMLInputElement).value).toBe('Keep this text');
  // A new response body is needed; fetch responses are consumed by json().
  fetcher.mockResolvedValue(Response.json({schema_version:'1',frontend_transport:'polling',formats:['pdf']}));
  fireEvent.change(within(dialog).getByLabelText('Access token (shared server only)'),{target:{value:'replacement'}});
  await act(async()=>fireEvent.click(within(dialog).getByRole('button',{name:'Connect / retry'})));
  expect(authenticationRequired()).toBe(false);
  expect(screen.getByRole('textbox',{name:'Unsent'})).toBe(input);
  vi.unstubAllGlobals();
});

it('successful session replacement clears obsolete authentication diagnostics',async()=>{
  render(<ApiErrors/>);
  act(()=>reportApiError(new ApiError(401,'authentication_required',{requestId:'auth-id'})));
  expect(screen.getByRole('alert')).toBeTruthy();
  act(()=>setAccessToken('synthetic-session'));
  expect(screen.queryByRole('alert')).toBeNull();
});
