# ◇ MightShape team workshops

Optional Slack, Discord, and Microsoft Teams adapters for MightShape 1.0.1.

One teammate can start a structured exercise in a channel. Other people explicitly contribute—or pass—through platform-native forms. The openly disclosed AI facilitator freezes protected divergence before synthesis, publishes meaningful progress checkpoints, and posts the same whimsical, source-linked PNG plus an accessible text alternative on every platform.

This is one collaboration service with three thin transports:

```text
Slack interactions ─┐
Discord interactions ├─ shared workshop state → facilitator → Visual Workbench
Teams activities ───┘          │                        │
                               └─ portable JSON          └─ PNG + text fallback
```

The Codex and Claude plugins remain fully usable without this service. Installing either plugin does not deploy a bot or grant access to a team workspace.

## Product boundaries

- Only slash commands, mentions, buttons, and submitted dialogs enter a workshop. There is no ambient channel surveillance.
- A person opts in through an explicit contribution or Pass action. The initiator cannot consent for the channel.
- Teammate input is `USER_PROVIDED` design material, not `HUMAN_INTERVIEW` or observed behavior.
- `SEALED` rounds reveal counts only until an authorized freeze. Wording and partial synthesis remain hidden.
- Raw tenant, workspace, guild, channel, message, and user identifiers remain in a private adapter binding. Portable exports use opaque `TP-*` and `UC-*` IDs.
- Visuals preserve source IDs, provenance, contradictions, and outliers. Upload failure never erases the text fallback.
- The default mock facilitator is honest: it renders a source wall and makes no semantic-clustering claim.

Supported exercises are brainwriting, brainstorming, affinity clustering, process reconstruction, assumption mapping, POV/HMW development, prototype design, and test design. Facilitation starts at `NOVICE_ASSISTED`, with one purpose, one mindset cue, and one bounded prompt.

## Run the shared checks

Node.js 22.13+, Python 3, and the repository checkout are required.

```bash
cd collaboration-app
npm ci
npm run typecheck
npm test
npm audit --omit=dev
```

Copy [`.env.example`](.env.example) into an untracked local secret configuration. `DC_AI_MODE=mock` needs no model credential. `DC_AI_MODE=openai` requires a server-side `OPENAI_API_KEY`; Responses API calls use `store: false` and receive the bounded frozen workshop packet. The `DC_*` configuration prefix is a compatibility contract for existing deployments and portable workshop records; it does not represent the current product name.

Platform setup:

- [Slack](docs/slack.md): `/design-think`, Socket Mode, external file-upload flow.
- [Discord](docs/discord.md): signed HTTP interactions, `/design-think`, no Gateway or Message Content intent.
- [Microsoft Teams](docs/teams.md): standard team channels, current Teams SDK, Adaptive Card dialogs, manifest 1.29.

## Storage and operations

The bundled `FileWorkshopStore` keeps the portable session and private platform binding in physically separate owner-only files. An atomic commit pointer selects a complete generation, independent optimistic versions protect both halves, and event digests remain replay-safe for the workshop's full retention lifetime. It is a single-process implementation, not a horizontally scalable service. Each workshop has a retention expiry and an initiator-controlled delete path. Controller deletion attempts recorded platform-post/file cleanup first and retains retryable private receipts if any remote cleanup fails; local state is removed only after those effects are resolved. Configure the deployment scheduler to run `npm run purge-expired`; scheduled expiry removes local records and generated local artifacts only—it cannot remove platform posts without a live platform client. Channel posts otherwise follow the platform/operator retention policy.

Before multi-instance or public deployment, provide:

- a transactional shared `WorkshopStore` and shared idempotency receipts;
- a durable background-job queue;
- encrypted persistent storage, managed secrets, access controls, backups, and an operator-specific retention policy;
- HTTPS endpoints where required, monitoring that does not log participant text, and platform-specific review/install approval;
- an accurate public privacy notice and terms for the operator.

Slack Socket Mode, a Discord test guild, and Teams custom-app sideloading are practical test paths. They are not evidence of marketplace approval or enterprise compliance.

## Version

This directory follows the repository's `1.0.1` release version. The adapters are implementation-complete and deterministically tested; each still requires the operator's own platform registration, credentials, HTTPS deployment, and live-workspace acceptance testing before broad installation.
