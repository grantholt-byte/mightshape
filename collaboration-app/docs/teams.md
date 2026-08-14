# MightShape for Microsoft Teams

The Teams adapter runs the same platform-neutral workshop service used by Slack and Discord. It uses the current GA [`@microsoft/teams.apps`](https://microsoft.github.io/teams-sdk/) and [`@microsoft/teams.cards`](https://microsoft.github.io/teams-sdk/typescript/in-depth-guides/adaptive-cards/) SDKs, not the retired TeamsFx or Bot Framework application layers.

## 1.0.1 boundary

- Standard team channels only.
- One member starts an exercise by mentioning `@MightShape`.
- Other members opt in through **Add my input**, which opens a private Adaptive Card dialog.
- A member may explicitly **Pass this prompt**; no contribution is fabricated on their behalf.
- Sealed input is never echoed before the initiator freezes the set.
- Only the initiating member can freeze/synthesize or close the exercise.
- Synthesis runs asynchronously and returns to the same channel thread.
- The result includes an inline PNG, useful alt text, and a complete text fallback. LLM-generated facilitator messages use Teams' AI-generated-content label.
- The app does not request Microsoft Graph, resource-specific consent, `ChannelMessage.Read`, tenant-wide channel access, or permission to enumerate team members.
- Team input is `USER_PROVIDED` design material. It is not `HUMAN_INTERVIEW` evidence merely because several coworkers participated.

The manifest intentionally exposes only the `team` bot scope. Private and shared channels are excluded from this first adapter release because their access and disclosure boundaries differ.

## Register and package

1. Register a Teams bot with the [Teams Developer CLI](https://microsoft.github.io/teams-sdk/cli/commands/app/create/) or Microsoft Teams Developer Portal. Configure its HTTPS messaging endpoint as:

   ```text
   https://YOUR-HOST.example/api/messages
   ```

2. From `collaboration-app`, install and build:

   ```bash
   npm ci
   npm run build
   npm run build:teams-package -- --app-id YOUR-APP-GUID
   ```

   The package builder substitutes the public app ID, validates the least-privilege boundary, creates Teams-compliant 192×192 color and 32×32 transparent outline icons, and writes:

   ```text
   ../dist/teams/mightshape-teams-1.0.1.zip
   ```

3. Upload that ZIP as a custom app in the target Teams tenant. Custom-app upload must be allowed by its administrator.

The template is [`manifest.template.json`](../manifests/teams/manifest.template.json). It targets Microsoft 365 app manifest schema 1.29 and contains no credentials.

## Run the service

Set credentials outside source control:

```bash
export CLIENT_ID="YOUR-APP-GUID"
export CLIENT_SECRET="YOUR-APP-SECRET"
export TENANT_ID="YOUR-TENANT-GUID"
export DC_AI_MODE="openai"
export OPENAI_API_KEY="YOUR-SERVER-SIDE-KEY"
export DC_TEAM_DATA_DIR="/private/path/mightshape-team-data"
npm run start:teams
```

The SDK listens on port `3978` by default and receives Teams activities at `/api/messages`. Use a trusted HTTPS tunnel for development or a normal HTTPS service for deployment. Never enable `DANGEROUSLY_ALLOW_UNAUTHENTICATED_REQUESTS` on a shared or public endpoint.

Use `DC_AI_MODE=mock` to test without a model call. Mock mode honestly renders a source wall and does not claim semantic clustering.

## Start and participate

In a standard channel:

```text
@MightShape start affinity | Where does our onboarding process lose context?
```

Supported exercise names include `brainstorm`, `brainwriting`, `affinity`, `process`, `assumptions`, `pov`, `prototype`, and `test`.

Teammates use **Add my input** on the workshop card. For accessibility, an open (non-sealed) session also accepts:

```text
@MightShape add TW-… The handoff from sales has no named owner.
@MightShape pass TW-…
```

The initiator can then use the card or mention commands:

```text
@MightShape freeze TW-…
@MightShape close TW-…
@MightShape delete TW-…
```

## Storage and deployment notes

The bundled file store is crash-safe and suitable for a single-process deployment. Put `DC_TEAM_DATA_DIR` on encrypted persistent storage, apply the retention policy appropriate to the team, and schedule `npm run purge-expired`. A multi-instance deployment should provide a transactional implementation of the shared `WorkshopStore` interface.

Teams activities are accepted promptly so the platform is not held open during synthesis or
delivery. There is therefore a narrow accept-before-receipt at-least-once edge if the process dies
between acknowledgement and durable claim. The durable service prevents ordinary replay after a
claim exists, but a production deployment that must eliminate this edge needs a transactional
ingress queue or equivalent platform receipt boundary.

The adapter collects only explicit mentions, card actions, and dialog submissions. It does not silently ingest surrounding channel history. Keep secrets, personal data, and confidential material out of workshop prompts unless the channel and deployment are approved for them.

## Official implementation references

- [Teams SDK quickstart](https://microsoft.github.io/teams-sdk/get-started/quickstart-build/)
- [Dialogs and private form input](https://microsoft.github.io/teams-sdk/typescript/in-depth-guides/dialogs/creating-dialogs/)
- [Threaded messages and sending](https://microsoft.github.io/teams-sdk/typescript/essentials/sending-messages/)
- [AI-generated bot-message labels](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content)
- [Microsoft 365 app manifest schema](https://learn.microsoft.com/en-us/microsoft-365/extensibility/schema/)
