import type { Evidence } from '../types/contract';

// Demo evidence. Excerpts were captured from the public pages listed in
// docs/challenge/PILOT_SCOPE.md on 18 Oct 2026 via a web fetch tool; check them
// against the live pages before relying on them. Real evidence will come from
// the backend's evidence store.

const BALLY = 'https://www.dbmr.unibe.ch/research/research_programs/bally_lab/index_eng.html';
const NUTRITION = 'https://www.artorg.unibe.ch/research/aihn/research_activities/intelligent_nutrition/index_eng.html';
const ADAPTIVE = 'https://www.artorg.unibe.ch/research/aihn/research_activities/adaptive_diabetes_management/index_eng.html';
const DCB_PROJECTS = 'https://www.dcberne.com/en/projects/';
const DCB_PROFS = 'https://www.dcberne.com/en/four-dcb-professorships-advance-research-in-diabetes-technology/';

const FETCHED = '2026-10-18';

const LABELS: Record<string, string> = {
  'ev-bally-therapy': 'Bally Lab · individualized therapy',
  'ev-bally-aid': 'Bally Lab · closed loop',
  'ev-bally-biomarkers': 'Bally Lab · digital biomarkers',
  'ev-adaptive-ai': 'ARTORG AIHN · AI care',
  'ev-adaptive-proactive': 'ARTORG AIHN · proactive care',
  'ev-gocarb-project': 'GoCARB project',
  'ev-gocarb-trial': 'GoCARB clinical trial',
  'ev-dcb-spn005': 'SPN-005 pilot study',
  'ev-dcb-aidjunct': 'AID-JUNCT study',
  'ev-dcb-menstrual': 'Menstrual Cycle Study',
  'ev-dcb-moonwalk': 'Moonwalk Project',
  'ev-dcb-porphyrin': 'Multi-metabolite sensing',
  'ev-dcb-network': 'DCB research network',
  'ev-bally-team': 'Bally Lab · team',
  'ev-aihn-contact': 'ARTORG AIHN · contact',
  'ev-dcb-profs-a': 'DCB professors · sensors & ML',
  'ev-dcb-profs-b': 'DCB professors · insulin therapy',
};

const BALLY_TEAM = 'https://www.dbmr.unibe.ch/research/research_programs/bally_lab/team/index_eng.html';
const AIHN = 'https://www.artorg.unibe.ch/research/aihn/index_eng.html';
const DCB_PRESS = 'https://www.pressetext.com/news/vier-professuren-staerken-den-forschungs-und-innovationsstandort-schweiz-in-der-diabetestechnologie.html';

const list: Omit<Evidence, 'n' | 'label'>[] = [
  {
    id: 'ev-bally-therapy',
    url: BALLY,
    title: 'Research: Bally Lab — Department for BioMedical Research (DBMR)',
    institution: 'UniBE',
    fetchedAt: FETCHED,
    excerpt: 'We strive to develop and apply state-of-the-art technologies for individualized therapy.',
    highlight: 'state-of-the-art technologies for individualized therapy',
    relevance: 'Shows the lab works on applying new technology to individual diabetes therapy, the space a sensor company sells into.',
  },
  {
    id: 'ev-bally-aid',
    url: BALLY,
    title: 'Research: Bally Lab — Department for BioMedical Research (DBMR)',
    institution: 'UniBE',
    fetchedAt: FETCHED,
    excerpt: '…our work on closed-loop automated insulin delivery systems, particularly in the hospital setting.',
    highlight: 'closed-loop automated insulin delivery systems',
    relevance: 'Closed-loop systems depend on continuous glucose data, so this group knows how sensor data is used clinically.',
  },
  {
    id: 'ev-bally-biomarkers',
    url: BALLY,
    title: 'Research: Bally Lab — Department for BioMedical Research (DBMR)',
    institution: 'UniBE',
    fetchedAt: FETCHED,
    excerpt: '…to develop and evaluate new digital biomarkers…',
    highlight: 'develop and evaluate new digital biomarkers',
    relevance: 'Evaluating digital biomarkers is directly relevant to validating what a wearable measures.',
  },
  {
    id: 'ev-adaptive-ai',
    url: ADAPTIVE,
    title: 'Adaptive Diabetes Management — ARTORG Center (AIHN)',
    institution: 'ARTORG',
    fetchedAt: FETCHED,
    excerpt: 'We develop AI approaches to enable more adaptive and personalised diabetes care.',
    highlight: 'AI approaches to enable more adaptive and personalised diabetes care',
    relevance: 'Algorithm expertise that could turn raw sensor readings into personalised guidance.',
  },
  {
    id: 'ev-adaptive-proactive',
    url: ADAPTIVE,
    title: 'Adaptive Diabetes Management — ARTORG Center (AIHN)',
    institution: 'ARTORG',
    fetchedAt: FETCHED,
    excerpt: 'Together, these efforts aim to shift diabetes care from reactive to proactive management while reducing daily burden.',
    highlight: 'from reactive to proactive management',
    relevance: 'Matches the company goal of reducing daily burden for people living with diabetes.',
  },
  {
    id: 'ev-gocarb-project',
    url: NUTRITION,
    title: 'Research: Intelligent Nutrition — ARTORG Center (AIHN)',
    institution: 'ARTORG',
    fetchedAt: FETCHED,
    excerpt: 'The system was developed within the framework of the GoCARB project.',
    highlight: 'GoCARB project',
    relevance: 'Names the project behind the meal carbohydrate estimation system.',
  },
  {
    id: 'ev-gocarb-trial',
    url: NUTRITION,
    title: 'Research: Intelligent Nutrition — ARTORG Center (AIHN)',
    institution: 'ARTORG',
    fetchedAt: FETCHED,
    excerpt: 'GoCARB was validated in a clinical trial involving individuals with T1D under sensor-augmented pump therapy.',
    highlight: 'validated in a clinical trial',
    relevance: 'Shows ARTORG has taken a diabetes digital tool through clinical validation, a step the company also faces.',
  },
  {
    id: 'ev-dcb-spn005',
    url: DCB_PROJECTS,
    title: 'Projects — Diabetes Center Berne',
    institution: 'DCB',
    fetchedAt: FETCHED,
    excerpt: 'SPN-005 – Pilot study on painless glucose monitoring. Towards painless, needle-free glucose monitoring for people with Type 1 Diabetes.',
    highlight: 'painless, needle-free glucose monitoring',
    relevance: 'Same goal as a non-invasive wearable sensor: glucose monitoring without needles.',
  },
  {
    id: 'ev-dcb-aidjunct',
    url: DCB_PROJECTS,
    title: 'Projects — Diabetes Center Berne',
    institution: 'DCB',
    fetchedAt: FETCHED,
    excerpt: 'AID-JUNCT study: GIP/GLP-1RA as Adjunctive to Automated Insulin Delivery',
    highlight: 'Automated Insulin Delivery',
    relevance: 'An active study on automated insulin delivery in Bern.',
  },
  {
    id: 'ev-dcb-menstrual',
    url: DCB_PROJECTS,
    title: 'Projects — Diabetes Center Berne',
    institution: 'DCB',
    fetchedAt: FETCHED,
    excerpt: 'Menstrual Cycle Study: Results published in Diabetes Care. DCB and Tidepool investigated how menstrual cycle phases relate to insulin needs, glycemic outcomes and insulin…',
    highlight: 'how menstrual cycle phases relate to insulin needs, glycemic outcomes',
    relevance: 'Confirms the lead you suggested: DCB has studied diabetes and the menstrual cycle.',
  },
  {
    id: 'ev-dcb-moonwalk',
    url: DCB_PROJECTS,
    title: 'Projects — Diabetes Center Berne',
    institution: 'DCB',
    fetchedAt: FETCHED,
    excerpt: 'The Moonwalk Project. Investigating the relationship between glucose values and motion patterns during sleep',
    highlight: 'glucose values and motion patterns during sleep',
    relevance: 'Combines glucose data with wearable motion data, close to what a multi-sensor wearable produces.',
  },
  {
    id: 'ev-dcb-porphyrin',
    url: DCB_PROJECTS,
    title: 'Projects — Diabetes Center Berne',
    institution: 'DCB',
    fetchedAt: FETCHED,
    excerpt: 'Illuminating Personalized Medicine. Porphyrin-based Aggregation-induced Emission Generating Molecules for Continuous Multi-Metabolite…',
    highlight: 'Continuous Multi-Metabolite',
    relevance: 'Early-stage sensing chemistry for continuous measurement of several metabolites; a possible future direction, not a glucose product.',
  },
  {
    id: 'ev-dcb-network',
    url: DCB_PROFS,
    title: 'Four DCB professorships advance research in diabetes technology — Diabetes Center Berne',
    institution: 'DCB',
    fetchedAt: FETCHED,
    sourceDate: '2026-04-10',
    excerpt:
      'Today, a total of 61 researchers work across the DCB professorships, reflecting the dynamic development of the centre. The Diabetes Center Berne is proud to provide a platform for this network of researchers.',
    highlight: '61 researchers work across the DCB professorships',
    relevance: 'Shows the size of the diabetes-technology research network a company could connect to in Bern.',
  },
];

// People. Names and roles exactly as the pages state them (captured 18 Oct 2026).
list.push(
  {
    id: 'ev-bally-team',
    url: BALLY_TEAM,
    title: 'Team: Bally Lab — Department for BioMedical Research (DBMR)',
    institution: 'UniBE',
    fetchedAt: FETCHED,
    excerpt: 'Dr. med. Dr. phil. Lia Bally — Group Leader. Dr. phil. David Herzig — Senior Researcher and Co-Group Leader.',
    highlight: 'Lia Bally — Group Leader',
    relevance: 'Names who leads the lab working on digital biomarkers and closed-loop insulin delivery.',
  },
  {
    id: 'ev-aihn-contact',
    url: AIHN,
    title: 'Research: AI in Health and Nutrition — ARTORG Center',
    institution: 'ARTORG',
    fetchedAt: FETCHED,
    excerpt:
      'Our research focuses on developing innovative AI-powered approaches for the personalized diagnosis and management … Contact: Prof. Dr. Stavroula Mougiakakou',
    highlight: 'Prof. Dr. Stavroula Mougiakakou',
    relevance: 'Listed as the contact for the AI-in-health group; the page does not state her formal role.',
  },
  {
    id: 'ev-dcb-profs-a',
    url: DCB_PRESS,
    title: 'Vier Professuren stärken den Forschungs- und Innovationsstandort Schweiz in der Diabetestechnologie (DCB, pressetext)',
    institution: 'DCB',
    fetchedAt: FETCHED,
    sourceDate: '2026-04-10',
    excerpt: 'Prof. Dr. Lilian Witthauer (Sensortechnologie), Prof. Dr. Lisa Koch (Data Science und Machine Learning)',
    highlight: 'Lilian Witthauer (Sensortechnologie)',
    relevance: 'Names the DCB professors for sensor technology and for data science / machine learning (German source).',
  },
  {
    id: 'ev-dcb-profs-b',
    url: DCB_PRESS,
    title: 'Vier Professuren stärken den Forschungs- und Innovationsstandort Schweiz in der Diabetestechnologie (DCB, pressetext)',
    institution: 'DCB',
    fetchedAt: FETCHED,
    sourceDate: '2026-04-10',
    excerpt: 'Prof. Dr. Maria Louisa Balmer (Mikrobiom und Stoffwechsel) und Prof. Dr. José Garcia (automatisierte Insulintherapie)',
    highlight: 'José Garcia (automatisierte Insulintherapie)',
    relevance: 'Names the DCB professor for automated insulin therapy (German source).',
  },
);

export const EVIDENCE: Record<string, Evidence> = Object.fromEntries(
  list.map((e, i) => [e.id, { ...e, n: i + 1, label: LABELS[e.id] }]),
);
