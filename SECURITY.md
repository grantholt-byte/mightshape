# Security policy

## Reporting

Do not open a public issue for a vulnerability that could expose participant data,
study links, credentials, or confidential project material. Use GitHub's private vulnerability
reporting for this repository at
`https://github.com/grantholt-byte/mightshape/security/advisories/new`. Include the affected
version, reproduction steps, impact, and the smallest safe proof. Do not include live participant
content. The maintainer aims to acknowledge a complete private report within five business days;
response and remediation timing depend on severity and reproducibility.

Use public GitHub issues only for non-sensitive bugs and support questions. If private
vulnerability reporting is temporarily unavailable, do not disclose sensitive details publicly;
contact the repository owner through a private channel shown on their GitHub profile.

## Security boundaries

- The core plugin is local and dependency-light. It has no required account, MCP server,
  telemetry service, Exchange backend, payment system, or remote database.
- Optional research may use network search. Queries and opened sources are handled by
  the active platform and its configured providers.
- The optional interview Site stores consent, anonymous participant IDs, interview state,
  and transcripts in its configured D1 database. `OPENAI_API_KEY` is server-only. Never
  expose `.dev.vars`, deployment secrets, researcher keys, or bearer study links in logs.
- A bearer study link grants participant access. Use high-entropy tokens, share narrowly,
  close studies after collection, and follow the configured retention/deletion policy.
- Disclosure Guard reduces accidental exposure; it is not legal review, an NDA, identity
  verification, or a confidentiality guarantee.
- Visual workshop artifacts are local derived files. The renderer escapes source text,
  embeds no third-party resources, and applies a restrictive content-security policy;
  preserve those controls when changing templates. Artifact access still exposes the
  underlying card content, so do not share a path or file beyond the intended audience.
- Plugin hooks execute with user trust. The supplied SessionStart hook is optional,
  read-only, time-bounded, and must never become a requirement for core behavior.
- Optional Slack, Discord, and Teams transports accept only explicit commands, mentions,
  component actions, and dialogs. Do not add channel-history access, Slack history scopes,
  Discord Message Content, or Teams Graph/RSC message-reading permissions for convenience.
- Store platform and model credentials only in the deployment secret manager. Default logs must
  never include interaction payloads, participant text, bearer tokens, signing secrets, or raw
  platform identifiers. Discord requests require current Ed25519 signatures and stale-request
  rejection; Teams must retain SDK authentication; Slack Socket Mode requires separate app- and
  bot-level tokens.
- The collaboration file store is owner-only and atomic, not encrypted or horizontally scalable.
  Multi-instance hosting requires a transactional shared store, shared replay receipts, a durable
  job queue, encrypted persistence, access controls, and an operator-specific privacy/retention
  policy. Schedule `npm run purge-expired` and test deletion before inviting a real team.
- Rendered team visuals reproduce workshop content and are uploaded to the selected platform.
  Treat the PNG and text alternative as sensitive as their source notes. Keep mention suppression,
  bounded input sizes, external-upload validation, and platform attachment limits intact.

## Sensitive research

Do not use the supplied Site for protected health information, payment-card data,
financial transactions, or interviews with children below the applicable digital-consent
age. Avoid secrets, source code, confidential strategy, personal identifiers, and
unnecessary proprietary details in participant-facing packets. Deployment owners are
responsible for legal, security, retention, access-control, and consent obligations.

## Dependencies and release checks

Python core helpers use the standard library; `jsonschema` is a development validator.
The optional Site and collaboration service have pinned lockfiles. Before release run:

```bash
make release-check
cd interview-app && npm audit --omit=dev
cd collaboration-app && npm audit --omit=dev
```

Review audit output rather than applying broad automated upgrades. Report dependency
findings with package, affected version, reachable path, and mitigation.
