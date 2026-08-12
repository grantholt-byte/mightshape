# Design Council — Live Interview Companion

The optional Sites-hosted extension for **◇ Design Council**. It lets a research
team share a high-entropy link with a real participant and conduct a transparent,
adaptive text interview with an AI facilitator.

The core Design Council skill does not depend on this app. If Sites hosting or an
OpenAI API key is unavailable, researchers can still prepare and conduct human-led
fieldwork from the core plugin.

## Participant safeguards

- Explicit, study-specific consent before any transcript is created.
- Clear disclosure that the interviewer is AI, never a human impersonation.
- Anonymous `P-###` participant IDs; names and emails are not required.
- Study purpose, approximate duration, collection terms, reviewers, quotation
  policy, retention, stop, and deletion rights shown before consent.
- High-confidence email/phone redaction before persistence. This is intentionally
  described as limited—not comprehensive anonymization.
- `SOLUTION_BLACKOUT` omits the proposed concept from the model prompt as well as
  the UI. `CONCEPT_REVEAL` is a deliberate, recorded transition.
- Participant messages retain `HUMAN_INTERVIEW` provenance. AI facilitator
  messages are stored separately as `AI_FACILITATOR` and are not research evidence.
- Skipping is a first-class `PARTICIPANT_ACTION`, not a fabricated interview
  response; skipped topics remain uncovered and the interviewer moves on neutrally.
- Stop preserves the transcript; delete removes the participant row and cascades
  the transcript, leaving only a content-free deletion receipt.
- Responses API requests use `store: false` and a privacy-preserving safety ID.

Participants should still avoid entering personal or confidential details. The
consent screen and `/privacy` page state this plainly.

## Architecture

- Official Sites `vinext` starter and Cloudflare Worker-compatible ESM output.
- Cloudflare D1 (`DB`) for studies, consent/session state, transcripts, events, and
  deletion receipts. R2 is intentionally disabled.
- Raw prepared D1 statements behind `lib/repository.ts`; Drizzle owns the schema and
  generated migrations.
- OpenAI Responses API called only from the server. Default model:
  `gpt-5.6-sol`; structured output, low reasoning effort, `store: false`.
- Deterministic mock interviewer for local validation and automated tests.
- No analytics SDK, auth framework, client database, or extra runtime dependency.

The public study token and participant session token are independent 256-bit bearer
secrets. Only SHA-256 hashes are persisted. Participant credentials live in tab
session storage, while all authoritative state lives in D1.

## Local development

Requirements: Node.js 22.13 or newer.

```bash
npm install
npm run db:generate
cp .env.example .env.local
npm run dev
```

For offline/local interviewing set:

```dotenv
INTERVIEW_AI_MODE=mock
```

For the live interviewer configure server-side values only:

```dotenv
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.6-sol
INTERVIEW_AI_MODE=openai
```

Never expose `OPENAI_API_KEY` through a `NEXT_PUBLIC_` variable. Configure hosted
runtime values through Sites rather than committing `.env` files.

## Researcher authorization and study creation

Researcher endpoints deny access by default. They accept either:

1. a Sites-injected ChatGPT identity present in
   `RESEARCHER_ALLOWED_USER_IDS` / `RESEARCHER_ALLOWED_EMAILS`; or
2. a high-entropy `RESEARCHER_API_KEY`, intended for the included seed script.

`RESEARCHER_ALLOW_ANY_AUTHENTICATED=true` is available for a workspace that has an
appropriate Sites access policy, but an explicit allowlist is safer. SIWC identity
alone is authentication, not proof of workspace membership.

Create a default blackout study:

```bash
RESEARCHER_API_KEY='...' npm run seed:study -- http://localhost:3000
```

Override fields with `STUDY_TITLE`, `STUDY_PURPOSE`, `STUDY_RESEARCH_GOAL`,
pipe-separated `STUDY_TOPICS`, `STUDY_DURATION_MINUTES`,
`STUDY_RETENTION_DAYS`, `STUDY_MAX_PARTICIPANTS`, and `STUDY_MAX_TURNS`.

Researcher API:

- `POST /api/researcher/studies` — create; returns the participant link once.
- `GET /api/researcher/studies/:id` — provenance-preserving JSON export.
- `PATCH /api/researcher/studies/:id` — `close` or one-way `reveal_concept`.
- `DELETE /api/researcher/studies/:id` — remove the study and its transcripts.

Participant API is scoped under `/api/studies/:publicToken` and requires a separate
participant session bearer token after consent.

## Validation

```bash
npm test
npm run build
npm run test:full
npm run lint
npm run typecheck
```

`npm run test:full` builds the Cloudflare ESM bundle, runs deterministic behavioral
tests, and checks server-rendered routes and security headers.

`npm audit --omit=dev` should report zero production vulnerabilities. The current
Sites/Vinext and migration toolchain still reports development-only advisories in
upstream build dependencies; those packages are not shipped as application runtime
dependencies.

With a local server running in mock mode, capture the two participant surfaces as
real browser renders:

```bash
E2E_BASE_URL=http://localhost:4173 \
RESEARCHER_API_KEY=your-local-researcher-key \
npm run test:screenshots
```

The command creates and cleans up its own D1 fixture study, drives installed
Chrome over the DevTools protocol, and writes `tests/screenshots/consent.png`
and `tests/screenshots/active.png` for visual inspection. Set `CHROME_PATH` on
systems where Chrome is installed elsewhere.

## Hosting boundary

`.openai/hosting.json` declares logical D1 binding `DB`; Sites owns the real database
and deployment wiring. Apply the packaged Drizzle migration and configure secrets
when publishing. No deployment is performed by this repository.

Retention is enforced as an access expiration and disclosed to participants. V1
does not include a scheduled purge worker because Sites scheduling is outside this
companion's deployment contract; researchers must delete expired studies or add a
platform-approved scheduled cleanup before regulated use. This app is a research
aid, not a compliance certification or substitute for institutional review.
