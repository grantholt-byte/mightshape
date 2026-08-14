# Team-channel workshops

Use this reference when MightShape facilitates a collaborative exercise in Slack, Discord, Microsoft Teams, or another shared messaging surface. The channel adapter is optional hosted infrastructure over the canonical MightShape method, evidence, participation, and visual contracts.

## Invariants

1. One member may initiate an exercise; initiation never grants that person the ability to consent for everyone else.
2. Teammates opt in through an explicit button, form/dialog, or direct mention. Do not ingest unrelated channel history or silently monitor a channel.
3. Every teammate contribution is `USER_PROVIDED` design material. It is not `HUMAN_INTERVIEW` or `OBSERVED_HUMAN_BEHAVIOR` unless separately collected through a consented Inquiry Lab study.
4. Preserve the contributor's words with a stable `UC-` ID. AI labels, clusters, summaries, and facilitator prompts are `DESIGN_COUNCIL`.
5. Keep raw workspace, channel, message, tenant, guild, and user identifiers in a private adapter binding. Portable workshop and project exports use opaque `TP-` participant IDs.
6. Make the AI role, visibility rule, model-provider processing, retention date, and delete path visible at launch. A public or cross-organization channel is not confidential.
7. Do not use channel contributions for model training. Never request secrets, credentials, health data, financial data, or proprietary detail unnecessary for the exercise.
8. Show milestones and artifact transformations, not hidden reasoning or token-by-token model output.
9. Apply least privilege. Platform convenience never overrides participant privacy or Council independence.
10. The Codex/Claude skill remains fully usable when every team adapter is absent or unavailable.

## Shared interaction model

Use one root message and its thread/conversation as the visible workshop boundary:

`start → orient → collect → freeze when required → synthesize → render → review → next move or close`

The initiator controls freeze, phase advance, pause, close, and delete by default. They may explicitly delegate facilitation. Any participant may add input, pass, request point-of-use help, or leave. Do not require a separate join step before a first contribution; the explicit contribution action is sufficient opt-in.

At setup collect only:

- challenge or current decision;
- starting point: early hunch, grounded exploration, framed challenge, concept, prototype, live, or unsure;
- named exercise;
- `OPEN` or `SEALED` input visibility;
- optional time/stop boundary.

Use `NOVICE_ASSISTED` unless the group demonstrates fluency. State the immediate purpose and mindset in plain language, give one method-safe example only when it will not anchor protected ideation, then ask one bounded prompt.

## Open and sealed participation

Use `SEALED` by default for protected brainstorming, brainwriting, premise challenge, or another activity where earlier submissions could anchor later contributors. Before freeze, display counts and operational status only. Do not reveal wording, names, reactions, partial clusters, or facilitator preference.

Use `OPEN` when visible co-construction is the method—for example collaborative affinity moves, process reconstruction, prototype decisions, or a critique after divergence. Clearly tell contributors that their submitted text will appear in the channel thread.

Freeze is immutable for that contribution set. New input received afterward either enters a named next round or a post-freeze challenge; never mutate the frozen set silently. If a Council Round A is also running, user input follows the stricter sealed-Council rule and reaches every selected member equally or waits until post-freeze.

## Group facilitation

- Separate participant, facilitator, and decision authority. Seniority, volume, speed, or platform role does not make one contribution stronger evidence.
- Use independent capture before open discussion when hierarchy, anchoring, or uneven airtime matters.
- Offer pass/skip without explanation. Never pressure personal disclosure.
- Batch progress updates. Show `INPUTS → TRANSFORMATION → OUTPUT → WHAT CHANGED → NEXT` only at meaningful boundaries.
- Preserve boundary cards, contradictions, and outliers. A popular cluster is not consensus or prevalence.
- When a group stalls, change stimulus, representation, or participation structure before changing the method.
- End when the learning boundary is reached, not because every template field is filled.

## Visual delivery

Every graphical channel artifact derives from the canonical `visual-artifact.schema.json` and retains source-card IDs, provenance labels, contradictions, limitations, and a text fallback. Render platform-safe PNG for inline display while keeping the canonical HTML, SVG, Markdown, input hash, and manifest in the artifact store.

The PNG may use MightShape's tactile sticky notes, tape, folded corners, playful neighborhoods, doodles, and lively process lanes. Decoration never encodes evidence status by itself. Always attach meaningful alt text and a concise text equivalent. Do not render a fresh image after every contribution; publish milestone boards when the source set, arrangement, frame, or decision materially changes.

If upload or image rendering fails, post the complete text fallback and preserve the artifact for retry. A missing image must not erase or relabel contributions.

## Platform boundaries

### Slack

Prefer `/design-think`, a global shortcut, explicit app mentions, Block Kit actions, and modals. Keep the exercise in one thread. Do not request `channels:history` or `groups:history` merely to capture free-form replies. Upload PNG through `files.getUploadURLExternal` followed by `files.completeUploadExternal`; never use the retired `files.upload` method.

### Discord

Prefer guild-installed application commands, buttons, and per-user modals through an HTTP interactions endpoint. This avoids the privileged Message Content intent. A workshop may live in a public thread. Verify every Ed25519 interaction signature, acknowledge or defer within three seconds, sanitize mentions, and upload the PNG as an attachment with a description plus text fallback.

### Microsoft Teams

Prefer direct `@MightShape` initiation and Adaptive Card/dialog contribution actions in a standard team channel. Do not request resource-specific consent to read every channel message. Use the current Microsoft Teams SDK rather than deprecated TeamsFx or the unsupported Bot Framework SDK. Keep activity in the originating thread, add the native AI-generated label to facilitator output, and include a compact text equivalent with any PNG.

## State and resilience

Use `team-workshop-session.schema.json` for the portable session and `team-channel-binding.schema.json` for private platform routing. Persist them separately. Store only digests of processed event IDs in portable logic and deduplicate retries before mutation. Use optimistic versions so simultaneous freeze or advance actions yield one transition.

Record outbound platform messages/files in the private binding. A delivery retry from `REVIEW`
must reload and hash-check the immutable saved artifact; it must never rerun synthesis. Controller
deletion attempts recorded remote cleanup before removing local state. If any cleanup fails, retain
the private receipts and local record for an explicit retry, and describe the deletion as partial.

The bundled file store is a single-process beta implementation with atomic owner-only files. A multi-instance deployment must supply a transactional `WorkshopStore` and durable background job queue. Never describe the development store as horizontally scalable.

Keep a retention expiry and initiator-controlled delete action. Event replay digests belong only in the private adapter binding, never in the portable workshop record. Scheduled expiry removes local records and generated local artifacts; it cannot remove platform posts without a live platform client. Delete adapter state and generated channel artifacts according to the disclosed policy; retain no content-free analytics beyond what the public privacy policy permits.

## Visible checkpoints

Use compact messages such as:

```text
◇ OPEN STUDIO · PROTECTED BRAINSTORM
12 participants · 9 sealed contributions
No submissions have been revealed.

NOW
Independent capture

NEXT
Initiator freezes the set, then MightShape reveals the source wall and clusters it.
```

After freeze:

```text
◇ WORKSHOP TRACE · SET FROZEN
9 USER_PROVIDED contributions · frozen before synthesis

TRANSFORMATION
Affinity clustering · contradictions and outliers preserved

OUTPUT
VA-004 · PNG + accessible text fallback

↳ NEXT MOVE
Investigate the uncertainty that most sharply separates the two leading frames.
```
