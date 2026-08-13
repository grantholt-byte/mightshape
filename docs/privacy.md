# Privacy and data handling

This document describes the V1 architecture, not a warranty or a substitute for a
deployment-specific privacy notice.

## Core plugin

Design Council's canonical project record is the human-readable
`.design-council/project.json` file in the active project, with revision snapshots under
`.design-council/history/`. The plugin does not require a Design Council account, external
database, telemetry collector, Exchange backend, or remote memory service.

The active AI platform still processes prompts, opened files, and tool results under that
platform's terms and workspace settings. When Design Council performs external research,
search queries and retrieved pages go through the platform's configured research tools.
Do not assume “local state” means the model provider receives no content.

Synthetic interviews and Council responses are labeled synthetic or `DESIGN_COUNCIL`.
They do not become human evidence through agreement, repetition, or confidence.

If a user joins an exercise, their ideas, card moves, cluster names, process steps, and other
contributions are sent through the active AI platform like the rest of the conversation and may
be stored in local project state as `USER_PROVIDED`. They are design-process material, not
`HUMAN_INTERVIEW` or `OBSERVED_HUMAN_BEHAVIOR`. Participation is optional. Pause, hand-back,
and exit preserve prior records; “undo” supersedes a contribution for historical integrity
rather than erasing it. Do not enter sensitive material merely because the facilitator asks one
small prompt at a time.

`VISIBLE` and `WORKSHOP` responses may reproduce source-card text, method outputs, board changes,
and decision boundaries in the conversation. They do not intentionally expose private
chain-of-thought, raw tool logs, subagent messages, or partial sealed-round responses. This
output-control boundary does not make the visible project content non-sensitive.

Visual workshop exports are written beneath `.design-council/artifacts/` as
self-contained HTML, SVG, Markdown, and a manifest. They are not uploaded by the
renderer and contain no remote fonts, scripts, analytics, or network requests. They
may still reproduce sensitive source-card text, so treat them with the same access,
disclosure, and retention rules as the underlying study material. Opening a local
artifact through a platform preview may cause that platform to process the file under
its own terms. Sticky-note colors, tape, doodles, rotation, and position are decorative;
they do not alter provenance, confidence, evidence strength, or privacy classification.

The optional A/B benchmark makes additional model calls and stores candidate responses,
usage counts, and blind-judge results in its selected local results directory. It is
opt-in and sends the benchmark prompts to the configured model provider; do not use
confidential project prompts unless that processing and local retention are acceptable.
The benchmark strips ambient service credentials from candidate subprocesses, but this is
process isolation rather than a claim of hardware, account, or provider isolation.

## Bring-Your-Own human interviews

The optional interview Site may store:

- the internal study definition and a minimized participant-facing packet;
- consent version and consent decision;
- opaque participant ID such as `P-001`;
- text transcript and adaptive interview state;
- stop, completion, retention, and deletion state.

Names and email addresses are off by default. Researchers should collect only what the
research question requires. Server-side interview calls use `store: false`; this does not
erase the Site's own D1 transcript record. Access controls, backups, logs, retention, and
deletion depend on the deployment configuration and operator.

Participant consent is independent from any project-owner research contribution setting.
Consent to one interview does not imply consent to train systems, publish quotes, or
contribute to future methodological research. De-identified quotations require the study's
applicable participant consent.

## Disclosure and proprietary material

Internal studies may contain strategy, proposed solutions, company context, assumptions,
or proprietary rationale. External Study Packets contain only participant-necessary
material. Disclosure Guard creates a separate sanitized candidate and never destroys the
internal original. It can reduce accidental exposure but cannot guarantee confidentiality,
legal privilege, trade-secret protection, conflict screening, or NDA enforceability.

## Exchange and Design Council Research

Design Council Exchange is a future provider boundary, not an operating marketplace in V1.
There is no participant recruitment, payment, credit ledger, identity verification,
reputation marketplace, or Exchange data transfer.

“Join Design Council Research” is future-facing and defaults off. No remote contribution
collector ships in V1. A future Learning Signal is designed to omit raw project content,
conversations, product ideas, code, files, company names, transcripts, and participant
quotes. Project-owner opt-in would never override participant consent.

Design Council Core does not sell confidential project content. A future hosted service
would require its own public policy, contracts, access controls, retention rules, and
consent model before processing data.

## Before public deployment

A publisher must provide a public, publisher-specific privacy policy with concrete controller identity,
purposes, data categories, recipients/processors, retention timelines, security measures,
rights/controls, contact route, and applicable regional terms. Replace this repository
architecture note with—or link it to—that reviewed policy in marketplace metadata. Do not submit
a raw GitHub rendering of this architecture note as if it were the final deployment policy.
