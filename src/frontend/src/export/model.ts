import type { BriefRevision, CaseDetail, Evidence, Institution, Reason, ReasonCategory } from '../types/contract';
import { INSTITUTION } from '../components/ui';

// One neutral model feeds both the PDF and the PowerPoint, so they always say the
// same thing. Only items she kept (✓ Keep) are exported, and only the sources those
// items cite, renumbered 1..n in order of first use. Hidden items, her chat,
// similar cases and the search trace are internal and never exported.

export interface ExportItem {
  category: ReasonCategory;
  headline: string;
  text: string;
  refs: number[];
  /** "Name · role" for people, entry names for the rest. */
  who: string;
  institution: string;
}

export interface ExportSource {
  n: number;
  title: string;
  institution: string;
  url: string;
  retrieved: string;
  published?: string;
  excerpt: string;
  highlight?: string;
}

export interface ExportModel {
  company: string;
  companySummary?: string;
  facts: string[];
  date: string;
  /** Up to three strongest kept items (groups/projects first, then people). */
  glance: ExportItem[];
  people: ExportItem[];
  groups: ExportItem[];
  projects: ExportItem[];
  infrastructure: ExportItem[];
  ideas: ExportItem[];
  questions: string[];
  introductions: { name: string; institution: string }[];
  sources: ExportSource[];
  snapshot: string;
  institutions: string[];
}

// Keyed by string so the export keeps working as categories are added to the contract.
export const CATEGORY_TITLE: Record<string, string> = {
  people: 'People',
  groups: 'Research groups',
  projects: 'Projects and studies',
  infrastructure: 'Infrastructure and services',
  ideas: 'Ideas to explore',
};

const instName = (i: Institution) => INSTITUTION[i].label;

export function kept(revision: BriefRevision): Reason[] {
  return revision.reasons.filter((r) => r.selection === 'kept');
}

export function buildExportModel(detail: CaseDetail, revision: BriefRevision): ExportModel {
  const keptReasons = kept(revision);
  const numbers = new Map<string, number>();
  const sources: ExportSource[] = [];
  const cite = (ids: string[]) =>
    ids
      .filter((id) => detail.evidence[id])
      .map((id) => {
        if (!numbers.has(id)) {
          const ev: Evidence = detail.evidence[id];
          numbers.set(id, numbers.size + 1);
          sources.push({
            n: numbers.size,
            title: ev.title.split(' — ')[0],
            institution: instName(ev.institution),
            url: ev.url,
            retrieved: ev.fetchedAt,
            published: ev.sourceDate,
            excerpt: ev.excerpt,
            highlight: ev.highlight,
          });
        }
        return numbers.get(id)!;
      });

  const item = (r: Reason): ExportItem => {
    const e = r.entries[0];
    return {
      category: r.category,
      headline: r.headline,
      text: r.line.text,
      refs: cite(r.line.evidenceIds),
      who: r.category === 'people' ? [e?.role].filter(Boolean).join('') : r.entries.map((x) => x.name).join(', '),
      institution: e ? instName(e.institution) : '',
    };
  };

  // Order of categories decides citation numbering: people, groups, projects, infrastructure, ideas.
  const by = (c: string) => keptReasons.filter((r) => (r.category as string) === c).map(item);
  const people = by('people');
  const groups = by('groups');
  const projects = by('projects');
  const infrastructure = by('infrastructure');
  const ideas = by('ideas');

  const glance = [...groups, ...projects, ...people].slice(0, 3);

  return {
    company: detail.case.companyLabel,
    companySummary: revision.company?.summary,
    facts: [...(revision.company?.facts ?? [])],
    date: new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }),
    glance,
    people,
    groups,
    projects,
    infrastructure,
    ideas,
    // Copies, never the live arrays: renderers (pdfmake) may rewrite what they are given.
    questions: [...revision.openQuestions],
    introductions: keptReasons
      .filter((r) => r.category === 'people' && r.entries[0])
      .map((r) => ({ name: r.entries[0].name, institution: instName(r.entries[0].institution) })),
    sources,
    snapshot: revision.coverage.snapshotDate,
    institutions: revision.coverage.institutions.map(instName),
  };
}

export const refText = (refs: number[]) => (refs.length ? ' ' + refs.map((n) => `[${n}]`).join('') : '');

export function fileSlug(company: string) {
  return company.replace(/[^a-z0-9]+/gi, '-').replace(/^-|-$/g, '').toLowerCase() || 'case';
}

export function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
