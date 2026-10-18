import type { Content, TDocumentDefinitions } from 'pdfmake/interfaces';
import logoUrl from '../assets/logo.png';
import { CATEGORY_TITLE, type ExportItem, type ExportModel } from './model';

// Company-facing "Why Bern" brief. Colours follow the partner template theme
// (accent1 #3C505A, accent6 #EA161F, dk2 #63737B). pdfmake and its fonts are
// bundled and loaded only when exporting, so this works offline.

const INK = '#3C505A';
const RED = '#EA161F';
const MUTED = '#63737B';
const LIGHT = '#F2F4F5';

async function dataUrl(url: string): Promise<string> {
  const blob = await (await fetch(url)).blob();
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result as string);
    r.onerror = reject;
    r.readAsDataURL(blob);
  });
}

const refs = (n: number[]): Content[] => (n.length ? [{ text: ' ' + n.map((x) => `[${x}]`).join(''), color: RED, fontSize: 8, bold: true }] : []);

function heading(text: string, extra: Partial<Record<string, unknown>> = {}): Content {
  return {
    margin: [0, 18, 0, 8],
    ...extra,
    columns: [
      { width: 4, canvas: [{ type: 'rect', x: 0, y: 1, w: 4, h: 14, color: RED }] },
      { text, style: 'h2', margin: [8, 0, 0, 0] },
    ],
  } as Content;
}

function itemBlock(it: ExportItem): Content {
  return {
    margin: [0, 0, 0, 10],
    unbreakable: true,
    stack: [
      { text: it.headline, bold: true, fontSize: 11.5, color: INK },
      ...(it.who || it.institution
        ? [{ text: [it.who, it.institution].filter(Boolean).join(' · '), fontSize: 9, color: MUTED, margin: [0, 1, 0, 2] } as Content]
        : []),
      { text: [it.text, ...refs(it.refs)], fontSize: 10, lineHeight: 1.25 },
    ],
  };
}

export async function buildPdf(model: ExportModel): Promise<Blob> {
  // pdfmake rewrites the content arrays it receives in place, so give it a private copy.
  const m: ExportModel = structuredClone(model);
  const [{ default: pdfMake }, fonts] = await Promise.all([import('pdfmake/build/pdfmake'), import('pdfmake/build/vfs_fonts')]);
  const f = fonts as unknown as { pdfMake?: { vfs: Record<string, string> }; vfs?: Record<string, string>; default?: unknown };
  (pdfMake as unknown as { vfs: unknown }).vfs = f.pdfMake?.vfs ?? f.vfs ?? (f.default as { pdfMake?: { vfs: unknown } })?.pdfMake?.vfs ?? f.default;

  const logo = await dataUrl(logoUrl);
  const content: Content[] = [];

  // Header and title
  content.push({
    columns: [
      { image: logo, width: 160 },
      { text: m.date, alignment: 'right', color: MUTED, fontSize: 9, margin: [0, 18, 0, 0] },
    ],
  });
  content.push({ text: 'BERN OPPORTUNITY BRIEF', color: RED, bold: true, fontSize: 9, characterSpacing: 1.2, margin: [0, 34, 0, 4] });
  content.push({ text: `Why Bern for ${m.company}`, style: 'h1' });
  content.push({ canvas: [{ type: 'line', x1: 0, y1: 4, x2: 483, y2: 4, lineWidth: 1, lineColor: '#D9DEE1' }], margin: [0, 6, 0, 14] });

  // Company box
  if (m.companySummary) {
    content.push({
      table: {
        widths: ['*'],
        body: [
          [
            {
              fillColor: LIGHT,
              margin: [12, 10, 12, 10],
              stack: [
                { text: m.company, bold: true, fontSize: 12, color: INK },
                { text: m.companySummary, fontSize: 10.5, margin: [0, 3, 0, 4] },
                ...(m.facts.length ? [{ text: m.facts.join('  ·  '), fontSize: 9, color: MUTED } as Content] : []),
              ],
            },
          ],
        ],
      },
      layout: 'noBorders',
    });
  }

  // At a glance
  if (m.glance.length) {
    content.push(heading('At a glance'));
    content.push({
      ol: m.glance.map((g) => ({ text: [{ text: g.headline + '. ', bold: true, color: INK }, g.text, ...refs(g.refs)], margin: [0, 0, 0, 5] })),
      fontSize: 10.5,
      markerColor: RED,
    } as Content);
  }

  // Categories
  for (const key of ['people', 'groups', 'projects', 'infrastructure'] as const) {
    const items = m[key];
    if (!items.length) continue;
    content.push(heading(key === 'people' ? 'People to know in Bern' : CATEGORY_TITLE[key]));
    items.forEach((it) => content.push(itemBlock(it)));
  }
  if (m.ideas.length) {
    content.push(heading(CATEGORY_TITLE.ideas));
    content.push({ text: 'Possible adjacent applications. They need to be validated with the experts.', italics: true, fontSize: 9, color: MUTED, margin: [0, -2, 0, 8] });
    m.ideas.forEach((it) => content.push(itemBlock(it)));
  }

  // Next steps
  if (m.questions.length || m.introductions.length) {
    content.push(heading('Next steps'));
    content.push({
      columns: [
        m.questions.length
          ? { width: '*', stack: [{ text: 'Questions to clarify', bold: true, fontSize: 10, color: INK, margin: [0, 0, 0, 4] }, { ul: m.questions, fontSize: 10 }] }
          : { width: '*', text: '' },
        m.introductions.length
          ? {
              width: '*',
              stack: [
                { text: 'Possible introductions', bold: true, fontSize: 10, color: INK, margin: [0, 0, 0, 4] },
                { ul: m.introductions.map((p) => `${p.name} (${p.institution})`), fontSize: 10 },
                { text: 'Availability not confirmed. The agency arranges contact.', italics: true, fontSize: 8.5, color: MUTED, margin: [0, 4, 0, 0] },
              ],
            }
          : { width: '*', text: '' },
      ],
      columnGap: 20,
    } as Content);
  }

  // Sources appendix
  if (m.sources.length) {
    content.push(heading('Sources', { pageBreak: 'before' }));
    content.push({
      text: `Every statement above cites one of these public pages. Retrieved ${m.snapshot} from ${m.institutions.join(', ')}.`,
      fontSize: 9,
      color: MUTED,
      margin: [0, -2, 0, 10],
    });
    for (const s of m.sources) {
      const i = s.highlight ? s.excerpt.indexOf(s.highlight) : -1;
      const quote =
        i < 0
          ? [s.excerpt]
          : [s.excerpt.slice(0, i), { text: s.highlight!, bold: true, color: INK }, s.excerpt.slice(i + s.highlight!.length)];
      content.push({
        margin: [0, 0, 0, 10],
        unbreakable: true,
        stack: [
          { text: [{ text: `[${s.n}] `, color: RED, bold: true }, { text: s.title, bold: true, color: INK, link: s.url }], fontSize: 10 },
          { text: s.url, link: s.url, fontSize: 8, color: '#2557c7', margin: [0, 1, 0, 1] },
          { text: [s.institution, `retrieved ${s.retrieved}`, s.published ? `published ${s.published}` : ''].filter(Boolean).join(' · '), fontSize: 8, color: MUTED },
          { text: ['“', ...quote, '”'], italics: true, fontSize: 9, margin: [8, 4, 0, 0], color: '#333' } as Content,
        ],
      });
    }
  }

  const doc: TDocumentDefinitions = {
    pageSize: 'A4',
    pageMargins: [56, 48, 56, 56],
    info: { title: `Why Bern for ${m.company}`, author: 'Bern Economic Development Agency', subject: 'Bern opportunity brief' },
    defaultStyle: { font: 'Roboto', fontSize: 10, color: '#1a1d23' },
    styles: {
      h1: { fontSize: 24, bold: true, color: INK },
      h2: { fontSize: 13, bold: true, color: INK },
    },
    content,
    footer: (page, pages) => ({
      margin: [56, 18, 56, 0],
      columns: [
        { text: `Bern Economic Development Agency · Public sources, retrieved ${m.snapshot}`, fontSize: 7.5, color: MUTED },
        { text: `${page} / ${pages}`, alignment: 'right', fontSize: 7.5, color: MUTED },
      ],
    }),
  };

  return new Promise((resolve) => pdfMake.createPdf(doc).getBlob((b: Blob) => resolve(b)));
}
