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

A publisher must provide a public privacy policy with concrete controller identity,
purposes, data categories, recipients/processors, retention timelines, security measures,
rights/controls, contact route, and applicable regional terms. Replace this repository
architecture note with—or link it to—that reviewed policy in marketplace metadata.
