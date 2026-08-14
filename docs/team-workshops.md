# Team-channel workshops — V1.0.1

MightShape's optional collaboration service lets one teammate initiate a structured exercise
in Slack, Discord, or Microsoft Teams. The shared engine owns methodology, state transitions,
sealed independence, evidence labels, facilitation, and visual rendering; each platform adapter
only maps native interactions to that engine.

```text
explicit team action
        ↓
Slack / Discord / Teams transport
        ↓
shared workshop state → bounded AI facilitator → canonical Visual Workbench
        ↓                         ↓
portable history             PNG + alt text + text fallback
```

| Surface | Start | Participation | Beta delivery | Ambient history |
|---|---|---|---|---|
| Slack | `/design-think` | Buttons and private modals | One thread; external PNG upload | Not requested |
| Discord | `/design-think start` | Buttons and per-user modals | Public thread when available; attachment PNG | No Gateway or Message Content |
| Teams | `@MightShape start …` | Adaptive Card action and private dialog | Standard-channel thread; inline card image | No Graph/RSC message read |

Teammate input is always `USER_PROVIDED` design material. It is not a customer interview,
observation, prevalence estimate, or other human-research evidence. Open exercises display
submissions in the thread. Sealed exercises display counts only until the initiator freezes the
complete input set. A participant may pass, and the facilitator never invents an answer for them.

The AI facilitator explains the immediate purpose, mindset, and one bounded next move for people
who do not already know Design Thinking. It publishes meaningful milestones and artifacts, not
private chain-of-thought or token-by-token narration. Source wording, source IDs, contradictions,
and outliers remain inspectable in the visual and its text equivalent.

## Set up a beta workspace

- [Slack setup](../collaboration-app/docs/slack.md)
- [Discord setup](../collaboration-app/docs/discord.md)
- [Microsoft Teams setup](../collaboration-app/docs/teams.md)
- [Shared service and operational boundary](../collaboration-app/README.md)

The Codex and Claude plugins do not deploy these bots. A host, platform registration, workspace or
tenant approval, and operator-controlled secrets are required. The included file store is suitable
for a single-process controlled beta only. No live workspace install has been certified merely by
the simulated interaction tests.

## Security and retention

Adapters receive only explicit commands, mentions, component actions, and submitted dialogs. Raw
platform identifiers stay in a separate owner-only binding; portable exports use opaque IDs.
Owner-only permissions are not encryption. Configure an appropriate retention period, schedule
`npm run purge-expired`, and keep platform/model tokens in a secret manager. Team threads and
uploaded images inherit the chosen platform's access and retention behavior. Controller deletion
uses durable outbound receipts for best-effort platform cleanup and retains a retryable local
record after any partial failure. Scheduled expiry removes local data only because it has no live
platform client.

Before multi-instance use, provide a transactional shared store, shared idempotency receipts,
durable background jobs, encrypted persistence, access controls, backups, content-safe monitoring,
an operator privacy notice, and a tested incident/deletion path.

## Current primary implementation references

- Slack: [app manifests](https://docs.slack.dev/app-manifests/), [slash commands](https://docs.slack.dev/interactivity/implementing-slash-commands), and [external file uploads](https://docs.slack.dev/reference/methods/files.getUploadURLExternal)
- Discord: [receiving interactions](https://docs.discord.com/developers/interactions/receiving-and-responding), [application commands](https://docs.discord.com/developers/interactions/application-commands), and [message components](https://docs.discord.com/developers/components/reference)
- Microsoft Teams: [Teams SDK quickstart](https://microsoft.github.io/teams-sdk/get-started/quickstart-build/), [dialogs](https://microsoft.github.io/teams-sdk/typescript/in-depth-guides/dialogs/creating-dialogs/), and [Microsoft 365 app manifest schema](https://learn.microsoft.com/en-us/microsoft-365/extensibility/schema/)

These are deployment transports, not OpenAI or Claude marketplace packages. Publication or review
on one platform does not approve another.
