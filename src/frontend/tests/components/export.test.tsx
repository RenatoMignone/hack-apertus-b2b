import { expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { Theme } from '@radix-ui/themes';
import ExportModal from '../../src/components/ExportModal';
import type { BriefRevision, CaseDetail } from '../../src/types/contract';
const {exportDeck, download}=vi.hoisted(()=>({exportDeck:vi.fn(),download:vi.fn()}));
vi.mock('../../src/api',()=>({api:{exportDeck},apiMode:'http'}));
vi.mock('../../src/export/model',()=>({kept:(r:BriefRevision)=>r.reasons.filter(x=>x.selection==='kept'),download,
  buildExportModel:vi.fn(),fileSlug:vi.fn()}));
const revision={id:'result',resultHash:'hash',reasons:[{id:'reason',headline:'Fictional',selection:'kept'}]} as BriefRevision;
const detail={case:{id:'case',companyLabel:'Fictional'},exportFormats:['pdf']} as CaseDetail;

it('double export clicks submit once and navigation prevents a late download',async()=>{
  let resolve!:(value:{filename:string;blob:Blob})=>void;
  exportDeck.mockReturnValue(new Promise(yes=>{resolve=yes;}));
  const close=vi.fn();const mounted=render(<Theme><ExportModal detail={detail} revision={revision} onClose={close} onConflict={vi.fn()} /></Theme>);
  const button=screen.getByRole('button',{name:/PDF brief/});fireEvent.click(button);fireEvent.click(button);
  expect(exportDeck).toHaveBeenCalledTimes(1);mounted.unmount();
  await act(async()=>resolve({filename:'test.pdf',blob:new Blob(['%PDF-test'])}));
  expect(download).not.toHaveBeenCalled();expect(close).not.toHaveBeenCalled();
});

it('export conflict requests refreshed review without downloading',async()=>{
  exportDeck.mockRejectedValue(new Error('stale'));const conflict=vi.fn();
  render(<Theme><ExportModal detail={detail} revision={revision} onClose={vi.fn()} onConflict={conflict} /></Theme>);
  await act(async()=>fireEvent.click(screen.getByRole('button',{name:/PDF brief/})));
  expect(conflict).toHaveBeenCalledTimes(1);expect(download).not.toHaveBeenCalled();
});
