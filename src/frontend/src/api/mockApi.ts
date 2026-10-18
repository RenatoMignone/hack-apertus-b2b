import type { NavigatorApi } from './index';
import type { BriefRevision, CaseDetail, DialogueTurn, Reason, RunStage, Selection } from '../types/contract';
import { emptyRevision, NETWORK_REASON, pruneTrace, reasonEvidence, SEED_CASES, TRACE_B } from '../mocks/cases';
import { EVIDENCE } from '../mocks/evidence';

// In-memory mock backend with scripted agent behaviour. Unknown instructions are
// acknowledged, never faked.

const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v));

// Demo state survives reloads via localStorage (per browser only). Evidence is
// static and re-attached on load rather than stored.
const KEY = 'bern-navigator-demo-v5';
type Saved = { cases: Omit<CaseDetail, 'evidence'>[] };

function loadSaved(): Saved | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Saved) : null;
  } catch {
    return null;
  }
}

const saved = loadSaved();
const store = new Map<string, CaseDetail>(
  (saved ? saved.cases.map((c) => ({ ...c, evidence: EVIDENCE })) : SEED_CASES.map((c) => clone(c))).map((c) => [c.case.id, c]),
);

function persist() {
  try {
    const cases = [...store.values()].map(({ evidence: _e, ...rest }) => rest);
    localStorage.setItem(KEY, JSON.stringify({ cases } satisfies Saved));
  } catch {
    // Storage blocked or full: the demo keeps working in memory.
  }
}

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const now = () => new Date().toISOString();
let seq = 0;
const uid = (p: string) => `${p}-${Date.now().toString(36)}-${++seq}`;

function get(id: string): CaseDetail {
  const c = store.get(id);
  if (!c) throw new Error(`Unknown case ${id}`);
  return c;
}

const current = (c: CaseDetail) => c.revisions.find((r) => r.id === c.currentRevisionId) ?? c.revisions[c.revisions.length - 1];

async function stages(onStage: (s: RunStage) => void, which: RunStage[] = ['interpreting', 'searching', 'validating', 'drafting']) {
  for (const s of which) {
    onStage(s);
    await wait(s === 'searching' ? 1200 : 700);
  }
  onStage('done');
}

const listeners = new Set<() => void>();
const emit = () => {
  persist();
  listeners.forEach((l) => l());
};

function touch(c: CaseDetail) {
  c.case.updatedAt = now();
  c.case.keptCount = current(c)?.reasons.filter((r) => r.selection === 'kept').length ?? 0;
  emit();
}

function addRevision(c: CaseDetail, base: BriefRevision, patch: Partial<BriefRevision>, note: string) {
  const reasons = patch.reasons ?? base.reasons;
  const rev: BriefRevision = {
    ...clone(base),
    changedReasonIds: [],
    ...patch,
    trace: patch.trace ?? pruneTrace(base.trace, reasonEvidence(reasons)),
    id: uid('rev'),
    version: Math.max(...c.revisions.map((r) => r.version)) + 1,
    parentId: base.id,
    createdAt: now(),
    changeNote: note,
  };
  c.revisions.push(rev);
  c.currentRevisionId = rev.id;
  return rev;
}

function say(c: CaseDetail, text: string, extra: Partial<DialogueTurn> = {}) {
  c.turns.push({ id: uid('t'), role: 'agent', text, createdAt: now(), ...extra });
}

const NUTRITION = /nutrition|meal|carb|food|diet|gocarb/i;

function seededFor(prompt: string): { rev: BriefRevision; topic: 'glucose' | 'insulin' | 'none'; health: boolean } {
  const p = prompt.toLowerCase();
  const first = (id: string) => clone(SEED_CASES.find((c) => c.case.id === id)!.revisions[0]);
  if (/glucose|sensor|cgm|wearable|monitor|menstrual|women/.test(p)) return { rev: first('case-glucowave'), topic: 'glucose', health: true };
  if (/insulin|pump|closed.?loop|\baid\b/.test(p)) return { rev: first('case-pumpline'), topic: 'insulin', health: true };
  const health = /diabet|medic|health|clinic|patient|bio|pharma|med ?tech|hospital/.test(p);
  return {
    rev: health
      ? emptyRevision('x', 'no_match', 'No reliable match in the indexed UniBE, ARTORG and DCB pages. Try other keywords.')
      : emptyRevision('x', 'out_of_scope', 'Outside life sciences. I only cover UniBE, ARTORG and DCB research.'),
    topic: 'none',
    health,
  };
}

function companyFrom(prompt: string) {
  const words = prompt.split(/[,.(\n]/)[0].trim().split(/\s+/);
  return (words.length > 3 ? words.slice(0, 3).join(' ') + '…' : words.join(' ')) || 'New case';
}

export const mockApi: NavigatorApi = {
  async listCases() {
    await wait(120);
    return [...store.values()].map((c) => clone(c.case)).sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  },

  async getCase(id) {
    await wait(100);
    const c = store.get(id);
    return c ? clone(c) : null;
  },

  async createCase(prompt) {
    const id = uid('case');
    const c: CaseDetail = {
      case: {
        id,
        companyLabel: companyFrom(prompt),
        oneLineNeed: prompt.length > 60 ? prompt.slice(0, 60) + '…' : prompt,
        status: 'researching',
        createdAt: now(),
        updatedAt: now(),
        keptCount: 0,
      },
      revisions: [],
      turns: [{ id: uid('t'), role: 'operator', text: prompt, createdAt: now() }],
      evidence: EVIDENCE,
    };
    store.set(id, c);
    emit();
    return clone(c);
  },

  async runCase(caseId, onStage) {
    const c = get(caseId);
    await stages(onStage);
    const { rev, topic } = seededFor(c.turns[0]?.text ?? '');
    rev.id = uid('rev');
    rev.createdAt = now();
    c.revisions = [rev];
    c.currentRevisionId = rev.id;
    c.case.status = rev.reasons.length ? 'in_review' : 'researching';
    if (topic === 'insulin') {
      say(c, 'First draft ready. One question:', {
        revisionId: rev.id,
        followUp: { id: uid('f'), question: 'R&D partner or clinical validation?', choices: ['R&D partner', 'Clinical validation', 'Both'] },
      });
    } else if (rev.reasons.length) {
      const people = rev.reasons.filter((r) => r.category === 'people').length;
      say(c, `Found ${people} people and ${rev.reasons.length - people} groups/projects. (Demo: seeded example for this topic.)`, { revisionId: rev.id });
    } else {
      say(c, 'Nothing reliable found, so no matches rather than guesses.', { revisionId: rev.id });
    }
    touch(c);
    return clone(c);
  },

  async sendMessage(caseId, text, onStage) {
    const c = get(caseId);
    c.turns.push({ id: uid('t'), role: 'operator', text, createdAt: now() });
    const base = current(c);
    const t = text.toLowerCase();

    if (!base) {
      await wait(400);
      say(c, 'No brief in this demo case. Start a new case to try the flow.');
      return clone(c);
    }

    const exclude = t.match(/(?:exclude|remove|drop|without|leave out|ignore|disregard|no more)\s+(?:the\s+)?(.+)/);
    if (exclude) {
      // Nutrition has synonyms in the seed; other topics match on their first significant word.
      const topic = exclude[1].replace(/[.!?]$/, '').trim();
      const word = NUTRITION.test(topic) ? null : topic.split(/\s+/).find((w) => w.length > 3) ?? topic;
      const matches = (r: Reason) => {
        const blob = (JSON.stringify(r) + r.entries.map((e) => e.evidenceIds.join(' ')).join(' ')).toLowerCase();
        return word ? blob.includes(word.toLowerCase()) : NUTRITION.test(blob);
      };
      const reasons = base.reasons.filter((r) => !matches(r));
      await stages(onStage, ['interpreting', 'drafting']);
      const label = word ?? 'nutrition';
      if (reasons.length === base.reasons.length) {
        say(c, `Nothing about “${label}” in this brief.`);
        return clone(c);
      }
      const rev = addRevision(c, base, { reasons }, `Removed ${label}`);
      say(c, `Removed ${base.reasons.length - reasons.length} item(s) about “${label}”.`, { revisionId: rev.id });
      touch(c);
      return clone(c);
    }

    if (/short|concise|condense|too long|fewer/.test(t)) {
      await stages(onStage, ['drafting']);
      const top = (cat: string) => base.reasons.filter((r) => r.category === cat).slice(0, 2);
      const rev = addRevision(c, base, { reasons: [...top('people'), ...top('groups'), ...top('projects')] }, 'Top 2 per section');
      say(c, 'Kept the 2 strongest items per section and dropped the ideas.', { revisionId: rev.id });
      touch(c);
      return clone(c);
    }

    const focus = t.match(/focus (?:only )?on (.+)/);
    if (focus) {
      const word = focus[1].replace(/[.!?]$/, '').trim().split(/\s+/)[0];
      await stages(onStage, ['interpreting', 'searching', 'drafting']);
      const reasons = base.reasons.filter((r) => JSON.stringify(r).toLowerCase().includes(word));
      if (!reasons.length) {
        say(c, `Nothing about “${word}” in the sources. Brief unchanged.`);
        return clone(c);
      }
      const rev = addRevision(c, base, { reasons }, `Focus: ${word}`);
      say(c, `Kept ${reasons.length} reason(s) about “${word}”.`, { revisionId: rev.id });
      touch(c);
      return clone(c);
    }

    await wait(700);
    if (/contact|meet|available|availability|willing|email|phone/.test(t)) {
      say(c, 'The pages name no contacts and say nothing about availability. That needs a call from the agency.');
    } else if (/simpl|explain|what does|what is|mean/.test(t)) {
      say(c, 'In short: DCB runs diabetes-tech studies, Bally Lab tests if new measurements are reliable, ARTORG builds AI for personalised advice.');
    } else {
      say(c, 'Demo: I understand “exclude …”, “focus on …” and “make it shorter”. Brief unchanged.');
    }
    touch(c);
    return clone(c);
  },

  async answerFollowUp(caseId, turnId, answer, onStage) {
    const c = get(caseId);
    const turn = c.turns.find((x) => x.id === turnId);
    if (turn?.followUp) turn.followUp.answer = answer;
    c.turns.push({ id: uid('t'), role: 'operator', text: answer, createdAt: now() });
    const base = current(c);
    if (!base) return clone(c);
    await stages(onStage);
    const clinical = /clinical|both/i.test(answer);
    const reasons = clinical ? [clone(NETWORK_REASON), ...base.reasons] : base.reasons;
    const rev = addRevision(
      c,
      base,
      {
        reasons,
        changedReasonIds: clinical ? [NETWORK_REASON.id] : [],
        openQuestions: base.openQuestions.filter((q) => !/R&D partner or clinical/i.test(q)),
        trace: pruneTrace(TRACE_B, reasonEvidence(reasons)),
        coverage: { ...base.coverage, resultKind: 'ok', limitations: [] },
      },
      answer,
    );
    say(c, clinical ? 'Added DCB’s research network for clinical studies.' : 'Kept the R&D-focused groups.', { revisionId: rev.id });
    c.case.status = 'in_review';
    touch(c);
    return clone(c);
  },

  async setSelection(caseId, itemId, selection: Selection) {
    const c = get(caseId);
    const r = current(c)?.reasons.find((x) => x.id === itemId);
    if (r) r.selection = selection;
    touch(c);
    return clone(c);
  },

  async setStatus(caseId, status) {
    const c = get(caseId);
    c.case.status = status;
    if (status !== 'closed') delete c.case.outcome;
    touch(c);
    return clone(c);
  },

  async setCurrentRevision(caseId, revisionId) {
    const c = get(caseId);
    c.currentRevisionId = revisionId;
    touch(c);
    return clone(c);
  },


  async setCaseFlags(caseId, flags) {
    const c = get(caseId);
    if ('onHold' in flags) c.case.onHold = flags.onHold;
    if ('outcome' in flags) c.case.outcome = flags.outcome;
    touch(c);
    return clone(c);
  },

  async resetDemo() {
    try {
      localStorage.removeItem(KEY);
    } catch {
      // ignore
    }
    store.clear();
    SEED_CASES.forEach((c) => store.set(c.case.id, clone(c)));
    emit();
  },

  subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};
