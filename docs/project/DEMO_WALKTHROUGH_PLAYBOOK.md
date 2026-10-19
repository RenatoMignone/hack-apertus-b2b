# Demo walkthrough playbook

**Status:** proposal, written 18 October 2026, to pick up when we build the demo.
Nothing here has been built or run for this project yet.

The goal is a single offline `index.html` that is both the pitch deck and the
live demo. Dark title and story slides alternate with short screen recordings of
our real frontend. Each clip plays, then freezes on its last frame with the next
control highlighted, and the presenter clicks it to continue. This gives the feel
of a live demo without the risk: no server, no network and no model calls on stage.

## Where this comes from

- **Voice note from a teammate (18 Oct 2026, 12:47).** Summary of the process
  they described: first build the frontend or simulation; then ask Claude for an
  HTML presentation and be very precise about the content of every slide and the
  transitions; then have the app itself embedded in the HTML as slides. For their
  BMW project, Claude first walked through the frontend and took a screenshot
  every few seconds. That was not smooth, so they switched to **screen
  recordings**. Recording took much longer, but the result was much better. A
  Streamlit dashboard was easier to embed for their other projects.
- **Reference implementation:** `rafay bmw.zip` (their `walkthrough/` folder),
  kept outside this repo at `C:\Users\m.kechiche\Downloads\rafay bmw.zip`. It is
  someone else's work: read it for the method only. Do not copy its branding,
  captions or media into our repository.

## How the BMW walkthrough works

Three Node scripts and a shell wrapper; the output is `index.html` + `media/`.

| Stage | File | What it does |
| --- | --- | --- |
| 1. Record | `tools/record.mjs` | Starts headless Chrome, connects to it over the Chrome DevTools Protocol (CDP) with a plain WebSocket (no Puppeteer or Playwright), sets a fixed 1440×900 viewport at a device scale factor of 4/3, and runs `Page.startScreencast` (JPEG, every frame). It then drives the real app step by step. |
| 2. Cut | `tools/encode.mjs` | Reads `timeline.json`, removes the trimmed waits, and writes an ffmpeg concat list per step → one 60 fps H.264 MP4 per step plus a `.webp` still of the step's last frame. |
| 3. Build | `tools/build.mjs` | Builds the HTML player as one template string: the CSS, the step list (slides + recorded shots) and the player JS, with the captions written next to it. Copies `media/`. |
| Wrapper | `tools/rec.sh`, `recapture.sh` | Copies the app to `/tmp`, resets its data, starts the server, records, encodes, builds (about 4 min). The repo's own data is never touched. |

### Tricks that make the recording look good

- **A fake cursor injected into the page:** an SVG arrow in a fixed-position
  `div`. It glides to each target with cubic easing, taking 380–950 ms depending
  on the distance, then shrinks and shows a ripple on click. The real click is
  sent separately with `Input.dispatchMouseEvent` at the same coordinates.
  `visualOnly` clicks move the cursor without clicking (used for a file drop zone).
- **Eased scrolling** with `requestAnimationFrame` so the target lands a set
  number of pixels below the top. No jumps.
- **Typing character by character** with `Input.insertText` and a short delay
  between characters.
- **Files** are set with `DOM.setFileInputFiles` (no OS dialog).
- **Trimmed waits:** while the app waits on the server/LLM, keep the first ~1.4 s
  of the spinner and cut the rest. The cuts are stored in `timeline.json` and
  applied in `encode.mjs`.
- **Step markers:** `mark(name, hotspotSelector, {focus})` records the end time of
  the step, the bounding box of the control to click next (the **hotspot**), and
  an optional **focus** box to zoom into. Boxes are stored as 0–1 fractions of the
  viewport, so the player scales them to any size. Recording fails if a hotspot is
  missing or off-screen, which is better than finding a broken hotspot on stage.
- **Stable targets:** before a step, the recorder tags the element it needs with
  `data-demo="1"` and finds it again with that selector. It does not rely on
  positions or `nth-child` selectors.
- **Simulated browser APIs:** headless Chrome has no microphone, so the recorder
  replaced `window.SpeechRecognition` with a fake that sends the words one at a
  time. The app's real dictation UI ran on top of it, and their Q&A script says
  openly that the speech input was simulated.
- **A time jump for the story:** between demo 1 and demo 2, the recorder moved the
  timestamps of the stored events back six months so that the "handover" was
  believable.

### How the player behaves

- Two stages: a dark **slide stage** (title, problem, quote, divider, close) and a
  light **shot stage**, which shows a 16:10 frame with a caption bar (step number,
  title, one line) and ←/Next buttons.
- Moving forward one step plays that step's clip. Back, a chapter jump or a deep
  link (`#12`) shows the still directly without playing.
- Two `<video>` elements alternate: the idle one preloads the next clip. Each
  clip starts on the previous step's last frame, so the switch from still to
  video is seamless.
- When a clip ends, the **camera** zooms with a CSS transform (scale up to 2.4×)
  to the focus box, if there is one. A pulsing blue **hotspot** button with a
  label appears over the next control, and its label is counter-scaled so it stays
  readable when zoomed.
- Keys: `→`/Space/Enter (pressed during a clip, they jump to its end), `←`,
  `Home`/`End`, `F` for full screen. Chapter tabs at the top and a progress bar.
- `prefers-reduced-motion` turns the animations off. Words of the quote slide
  appear one at a time with a blur.
- It needs no server: opening the file in Chrome is enough, as long as `media/` is
  next to it.

### How the presentation is written

- **`SCRIPT.md`** holds one table row per step: time, on screen, **say**, **click**,
  at about 150 words a minute, planned to finish ~15 s before the limit to leave
  time for clicks. It ends with prepared answers to likely judge questions
  ("Is the data real?", "Did you really speak?").
- **The story:** the brief solved (demo 1), then "that was the brief, and what every
  team built", a real user quote (used with consent), then a twist (demo 2,
  memory/handover) and a closing line. Showing the challenge, then the insight,
  is what made it memorable.

## Adapting it to our project

### Our app

- Vite + React in `src/frontend/`, on **mock data** (`src/frontend/src/mocks/`).
  Routes: `/` (Desk), `/cases`, `/cases/new`, `/cases/:id`, `/actions`.
- Start it with `npm run dev` in `src/frontend` (preview_start / launch.json in the
  desktop app). Mock data means there are no LLM waits to trim yet. Keep the
  trimming anyway in case a live backend is connected later.
- Add `data-demo-*` attributes or stable `id`s to the controls the recorder needs,
  instead of long CSS selectors. Mock data must be **deterministic** so that each
  re-recording gives the same scores and order.

### Windows differences (this machine)

- Chrome path: use `C:\Program Files\Google\Chrome\Application\chrome.exe`, or let
  Playwright's bundled Chromium do it. CDP over WebSocket works as is (Node 22 has a
  built-in `WebSocket` and `fetch`).
- `ffmpeg` 9.0.2 is installed via scoop (`~\scoop\shims\ffmpeg.exe`). `cwebp` is not
  installed: write the still with ffmpeg (`-frames:v 1 x.webp`) or use JPEG/PNG.
- Rewrite `rec.sh`/`recapture.sh` as PowerShell or Node scripts, and use a
  scratch/temp copy of the app instead of `/tmp`.
- In `encode.mjs` concat lists, use forward slashes in the `file '…'` paths.

### Constraints we must respect

- **Submission:** the demo video is **at most 2 minutes**. The pitch deck PDF is
  **at most 10 slides** (see [event and submission](EVENT_AND_SUBMISSION.md)). The
  HTML walkthrough is for the live pitch; record the 2-minute video *from the
  walkthrough*, and still export a ≤10-slide PDF of the slides.
- **Honesty:** the frontend is on mock data. Put a visible "mock data" or
  "illustrative" label wherever the results are not real retrieval output, and say
  it in the Q&A notes. Do not show people, roles or contact details as real unless
  they come from real cited public sources (AGENTS.md constraint 4).
- **No confidential input:** demo intake is typed keywords/context only, never
  a company business plan (constraint 5).
- **Three source families:** the walkthrough should visibly cover UniBE, ARTORG and
  Diabetes Center Berne (constraint 3), within the diabetes-technology pilot.
- **Branding:** check [data and provenance](../data/DATA_AND_PROVENANCE.md) and
  `docs/provided_material/` before using any partner logo or template.
- Do not claim air-gapped operation or measured quality in the slides unless it
  was actually tested.

### Proposed storyline (draft, to refine)

1. Title slide: the problem in one line (a Bern start-up looking for the right
   research partner).
2. A new case: type the permitted keywords/context (diabetes technology, for
   example closed-loop insulin delivery).
3. The run stepper/progress while the search runs.
4. Ranked matches across UniBE / ARTORG / DCB, each with its evidence and source.
5. Open the evidence drawer: the cited source behind one match, with a zoom.
6. "How I searched" Sankey: what was searched and filtered (zoom).
7. A no-match or limitation example, to show we do not invent results.
8. Export/next actions.
9. Closing slide: sovereignty (Apertus, self-hosted), the target architecture,
   what is real and what is mocked.

Total length: aim for ≤2:00 for the video version. The live pitch can be longer
if its duration is confirmed (currently **unknown**).

## Build checklist

1. Freeze the frontend flow and its mock data. Add `data-demo` hooks.
2. Write `SCRIPT.md` first: steps, captions, what to say, the hotspot for each
   step. Be precise about every slide and every transition (the voice note's main
   advice).
3. Write `record.mjs` for our flow (cursor, eased scrolling, typing, `mark()`
   with hotspot/focus, trimmed waits).
4. Write `encode.mjs` (clips + stills + `manifest.json`) and `build.mjs` (the
   player, with captions and slides in it).
5. Put the tools under `src/demo/walkthrough/` (code belongs in `src/`). Generated
   `media/` and `index.html` are build output: decide whether to commit them, as
   MP4s make the repository larger.
6. Rehearse with the script timer; record the ≤2-minute video from the
   walkthrough.

### Prompt to start the build with Claude

> Build an offline HTML demo walkthrough for `src/frontend`, following
> `docs/project/DEMO_WALKTHROUGH_PLAYBOOK.md`. Record the real app with headless
> Chrome over CDP (visible eased cursor, eased scrolling, typed input, one
> `mark()` per step with hotspot and focus boxes), cut one MP4 + still per step
> with ffmpeg, and build a player `index.html` with dark story slides, clips that
> freeze on a pulsing hotspot, zoom-to-focus, chapter tabs and keyboard controls.
> Here is the exact slide-by-slide script: …
