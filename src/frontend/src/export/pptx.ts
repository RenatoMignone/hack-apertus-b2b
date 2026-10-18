import JSZip from 'jszip';
import templateUrl from '../assets/export/partner-template.pptx?url';
import { CATEGORY_TITLE, type ExportItem, type ExportModel } from './model';

// Builds the deck from the partner's own PowerPoint template (challenge-only use,
// see docs/provided_material/README.md). The master, theme, fonts, logo and slide
// layouts are kept; the 19 example slides, their charts and notes are removed and
// replaced by our slides, which fill the layouts' real placeholders. The result is
// a normal, editable deck in the agency design.

// Layout files in the template (names from the template, German):
const L = {
  title: 'slideLayout1.xml', // Titelfolie
  chapterRed: 'slideLayout6.xml', // Kapiteltitel Rot
  content: 'slideLayout8.xml', // Titel und Inhalt
  subtitled: 'slideLayout9.xml', // Titel, Untertitel und Inhalt
  twoCol: 'slideLayout10.xml', // Zwei Inhalte
};

const RED = 'EA161F';
const INK = '3C505A';
const MUTED = '63737B';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

type Run = { text: string; b?: boolean; i?: boolean; color?: string; sz?: number; link?: string };
type Para = { runs: Run[]; lvl?: number; plain?: boolean };

interface SlideSpec {
  layout: string;
  title?: string;
  subtitle?: string;
  eyebrow?: string; // layout 1/9 body idx 13
  byline?: string[]; // layout 1 body idx 14
  body?: Para[];
  right?: Para[];
}

class SlideWriter {
  private links: string[] = [];
  private nextId = 2;

  constructor(private date: string, private footer: string) {}

  rels(layout: string) {
    const links = this.links
      .map((url, i) => `<Relationship Id="rId${i + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="${esc(url)}" TargetMode="External"/>`)
      .join('');
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/${layout}"/>${links}</Relationships>`;
  }

  private run(r: Run) {
    let link = '';
    if (r.link) {
      this.links.push(r.link);
      link = `<a:hlinkClick r:id="rId${this.links.length + 1}"/>`;
    }
    const attrs = [`lang="en-GB"`, r.sz ? `sz="${r.sz}"` : '', r.b ? 'b="1"' : '', r.i ? 'i="1"' : '', 'dirty="0"'].filter(Boolean).join(' ');
    const fill = r.color ? `<a:solidFill><a:srgbClr val="${r.color}"/></a:solidFill>` : '';
    return `<a:r><a:rPr ${attrs}>${fill}${link}</a:rPr><a:t>${esc(r.text)}</a:t></a:r>`;
  }

  private para(p: Para) {
    const ppr = p.plain ? '<a:pPr marL="0" indent="0"><a:buNone/></a:pPr>' : p.lvl ? `<a:pPr lvl="${p.lvl}"/>` : '';
    return `<a:p>${ppr}${p.runs.map((r) => this.run(r)).join('')}</a:p>`;
  }

  private sp(name: string, ph: string, paras: Para[]) {
    const id = this.nextId++;
    const body = paras.length ? paras.map((p) => this.para(p)).join('') : '<a:p><a:endParaRPr lang="en-GB" dirty="0"/></a:p>';
    return `<p:sp><p:nvSpPr><p:cNvPr id="${id}" name="${esc(name)} ${id}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr>${ph}</p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr><a:normAutofit/></a:bodyPr><a:lstStyle/>${body}</p:txBody></p:sp>`;
  }

  slide(s: SlideSpec) {
    const isTitle = s.layout === L.title || s.layout === L.chapterRed;
    const shapes: string[] = [];
    if (s.title) shapes.push(this.sp('Title', `<p:ph type="${isTitle ? 'ctrTitle' : 'title'}"/>`, [{ runs: [{ text: s.title }] }]));
    if (s.subtitle && isTitle) shapes.push(this.sp('Subtitle', '<p:ph type="subTitle" idx="1"/>', [{ runs: [{ text: s.subtitle }] }]));
    if (s.eyebrow) shapes.push(this.sp('Text', '<p:ph type="body" sz="quarter" idx="13"/>', [{ runs: [{ text: s.eyebrow }] }]));
    if (s.byline) shapes.push(this.sp('Text', '<p:ph type="body" sz="quarter" idx="14"/>', s.byline.map((t) => ({ runs: [{ text: t }] }))));
    if (s.body) shapes.push(this.sp('Content', '<p:ph idx="1"/>', s.body));
    if (s.right) shapes.push(this.sp('Content', '<p:ph idx="2"/>', s.right));
    shapes.push(this.sp('Date', '<p:ph type="dt" sz="half" idx="10"/>', [{ runs: [{ text: this.date }] }]));
    shapes.push(this.sp('Footer', '<p:ph type="ftr" sz="quarter" idx="11"/>', [{ runs: [{ text: this.footer }] }]));
    const num = this.nextId++;
    shapes.push(
      `<p:sp><p:nvSpPr><p:cNvPr id="${num}" name="Slide number ${num}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldNum" sz="quarter" idx="12"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:fld id="{442AD375-037F-43D0-B059-5172DA06796A}" type="slidenum"><a:rPr lang="en-GB"/><a:t>‹#›</a:t></a:fld></a:p></p:txBody></p:sp>`,
    );
    return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>${shapes.join('')}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>`;
  }
}

const refRun = (refs: number[]): Run[] => (refs.length ? [{ text: ' ' + refs.map((n) => `[${n}]`).join(''), color: RED, sz: 1200, b: true }] : []);

/** One item as: bold headline, a muted "who · institution" line, then the sentence with sources. */
function itemParas(it: ExportItem, size = 1600): Para[] {
  const who = [it.who, it.institution].filter(Boolean).join(' · ');
  return [
    { runs: [{ text: it.headline, b: true, color: INK, sz: size }] },
    ...(who ? [{ lvl: 1, runs: [{ text: who, color: MUTED, sz: size - 300 }] }] : []),
    { lvl: 1, runs: [{ text: it.text, sz: size - 200 }, ...refRun(it.refs)] },
  ];
}

const chunk = <T,>(xs: T[], n: number) => Array.from({ length: Math.ceil(xs.length / n) }, (_, i) => xs.slice(i * n, i * n + n));
const header = (text: string): Para => ({ plain: true, runs: [{ text, b: true, color: RED, sz: 1500 }] });

function planSlides(m: ExportModel): SlideSpec[] {
  const slides: SlideSpec[] = [
    {
      layout: L.title,
      eyebrow: 'Bern opportunity brief',
      title: `Why Bern for ${m.company}`,
      subtitle: m.companySummary ?? 'Research and expertise in the Canton of Bern',
      byline: ['Bern Economic Development Agency', m.date],
    },
  ];

  if (m.glance.length)
    slides.push({
      layout: L.content,
      title: 'At a glance',
      body: m.glance.map((g) => ({ runs: [{ text: g.headline + '. ', b: true, color: INK, sz: 1800 }, { text: g.text, sz: 1700 }, ...refRun(g.refs)] })),
    });

  chunk(m.people, 3).forEach((group, i) =>
    slides.push({ layout: L.content, title: i ? 'People to know in Bern (continued)' : 'People to know in Bern', body: group.flatMap((p) => itemParas(p)) }),
  );

  if (m.groups.length && m.projects.length) {
    const rows = Math.max(Math.ceil(m.groups.length / 3), Math.ceil(m.projects.length / 3));
    for (let i = 0; i < rows; i++) {
      const g = m.groups.slice(i * 3, i * 3 + 3);
      const p = m.projects.slice(i * 3, i * 3 + 3);
      slides.push({
        layout: L.twoCol,
        title: 'Research groups and projects',
        body: g.length ? [header(CATEGORY_TITLE.groups), ...g.flatMap((x) => itemParas(x, 1400))] : [],
        right: p.length ? [header(CATEGORY_TITLE.projects), ...p.flatMap((x) => itemParas(x, 1400))] : [],
      });
    }
  } else {
    for (const key of ['groups', 'projects'] as const)
      chunk(m[key], 3).forEach((group) => slides.push({ layout: L.content, title: CATEGORY_TITLE[key], body: group.flatMap((x) => itemParas(x)) }));
  }

  chunk(m.infrastructure, 3).forEach((group, i) =>
    slides.push({
      layout: L.content,
      title: i ? `${CATEGORY_TITLE.infrastructure} (continued)` : CATEGORY_TITLE.infrastructure,
      body: group.flatMap((x) => itemParas(x)),
    }),
  );

  chunk(m.ideas, 3).forEach((group) =>
    slides.push({
      layout: L.subtitled,
      title: CATEGORY_TITLE.ideas,
      eyebrow: 'Possible adjacent applications, to be validated with the experts',
      body: group.flatMap((x) => itemParas(x)),
    }),
  );

  if (m.questions.length || m.introductions.length) {
    const q: Para[] = m.questions.length ? [header('Questions to clarify'), ...m.questions.map((t) => ({ runs: [{ text: t, sz: 1600 }] }))] : [];
    const intro: Para[] = m.introductions.length
      ? [
          header('Possible introductions'),
          ...m.introductions.map((p) => ({ runs: [{ text: p.name, sz: 1600, b: true, color: INK }, { text: ` (${p.institution})`, sz: 1500 }] })),
          { plain: true, runs: [{ text: 'Availability not confirmed. The agency arranges contact.', i: true, color: MUTED, sz: 1200 }] },
        ]
      : [];
    slides.push(q.length && intro.length ? { layout: L.twoCol, title: 'Next steps', body: q, right: intro } : { layout: L.content, title: 'Next steps', body: [...q, ...intro] });
  }

  chunk(m.sources, 6).forEach((group, i) =>
    slides.push({
      layout: L.content,
      title: i ? 'Sources (continued)' : 'Sources',
      body: group.flatMap((s) => [
        { plain: true, runs: [{ text: `[${s.n}] `, b: true, color: RED, sz: 1300 }, { text: s.title, b: true, sz: 1300, link: s.url }] },
        { plain: true, runs: [{ text: `${s.institution} · retrieved ${s.retrieved} · `, color: MUTED, sz: 1100 }, { text: s.url, sz: 1100, link: s.url }] },
      ]),
    }),
  );

  slides.push({
    layout: L.content,
    title: 'Contact',
    body: [
      { plain: true, runs: [{ text: 'Bern Economic Development Agency', b: true, color: INK, sz: 2000 }] },
      { plain: true, runs: [{ text: '[Your name, function]', color: MUTED, sz: 1800 }] },
      { plain: true, runs: [{ text: '[Email · phone]', color: MUTED, sz: 1800 }] },
    ],
  });
  return slides;
}

export async function buildPptx(m: ExportModel): Promise<Blob> {
  const zip = await JSZip.loadAsync(await (await fetch(templateUrl)).arrayBuffer());

  // 1. Drop the example slides and everything only they used.
  const drop = /^ppt\/(slides|notesSlides|charts|embeddings|diagrams)\//;
  Object.keys(zip.files)
    .filter((p) => drop.test(p))
    .forEach((p) => zip.remove(p));

  let types = await zip.file('[Content_Types].xml')!.async('string');
  types = types.replace(/<Override PartName="\/ppt\/(slides|notesSlides|charts|embeddings|diagrams)\/[^"]*"[^>]*\/>/g, '');

  let presRels = await zip.file('ppt/_rels/presentation.xml.rels')!.async('string');
  presRels = presRels.replace(/<Relationship [^>]*Type="http:\/\/schemas\.openxmlformats\.org\/officeDocument\/2006\/relationships\/slide"[^>]*\/>/g, '');

  // 2. Write our slides.
  const footer = `Public sources · retrieved ${m.snapshot}`;
  const specs = planSlides(m);
  const ids: string[] = [];
  const newRels: string[] = [];
  const overrides: string[] = [];
  specs.forEach((spec, i) => {
    const n = i + 1;
    const w = new SlideWriter(m.date, footer);
    zip.file(`ppt/slides/slide${n}.xml`, w.slide(spec));
    zip.file(`ppt/slides/_rels/slide${n}.xml.rels`, w.rels(spec.layout));
    const rid = `rIdNav${n}`;
    newRels.push(`<Relationship Id="${rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${n}.xml"/>`);
    ids.push(`<p:sldId id="${255 + n}" r:id="${rid}"/>`);
    overrides.push(`<Override PartName="/ppt/slides/slide${n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`);
  });

  zip.file('[Content_Types].xml', types.replace('</Types>', overrides.join('') + '</Types>'));
  zip.file('ppt/_rels/presentation.xml.rels', presRels.replace('</Relationships>', newRels.join('') + '</Relationships>'));

  let pres = await zip.file('ppt/presentation.xml')!.async('string');
  pres = pres.replace(/<p:sldIdLst>[\s\S]*?<\/p:sldIdLst>/, `<p:sldIdLst>${ids.join('')}</p:sldIdLst>`);
  zip.file('ppt/presentation.xml', pres);

  const app = zip.file('docProps/app.xml');
  if (app) {
    const xml = (await app.async('string')).replace(/<Slides>\d+<\/Slides>/, `<Slides>${specs.length}</Slides>`).replace(/<Notes>\d+<\/Notes>/, '<Notes>0</Notes>');
    zip.file('docProps/app.xml', xml);
  }

  return zip.generateAsync({ type: 'blob', mimeType: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', compression: 'DEFLATE' });
}
