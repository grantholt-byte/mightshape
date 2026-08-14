# MightShape for Slack — 1.0.1

The Slack adapter lets one member start a MightShape exercise and lets teammates participate from a single channel thread. It is an optional surface over the shared workshop service; it does not fork the methodology or portable project state.

## What works in 1.0.1

- `/design-think` opens a setup modal with challenge, exercise, idea stage, and open/sealed contribution mode.
- One root message becomes the exercise boundary. Teammates contribute through explicit buttons and modals.
- Sealed contributions remain hidden until the initiator freezes the round. Open contributions appear in the thread as they arrive.
- Only the initiator (or a future explicitly delegated facilitator) can freeze or close the exercise; authorization is enforced by the shared service, not by hidden UI state.
- Interactive requests are acknowledged before persistence, synthesis, rendering, or upload work begins.
- The frozen set is synthesized by the disclosed AI facilitator. Every teammate input remains `USER_PROVIDED`, never `HUMAN_INTERVIEW`.
- Source-linked affinity or process artifacts are rendered as PNG, uploaded into the exercise thread, and accompanied by alt text and a plain-text alternative.
- PNG delivery uses `files.getUploadURLExternal` → external byte upload → `files.completeUploadExternal`. The retired `files.upload` method is never used.
- **Retry delivery** reuses the immutable saved artifact; it does not spend another synthesis call.
- **Delete workshop data** attempts to remove every recorded bot post/file before deleting local state. Partial remote failure is reported and retained for an explicit retry with `/design-think delete TW-…`.

The app does not subscribe to channel messages and does not request channel-history scopes. It only receives slash commands, button interactions, and modal submissions that people explicitly send to it.

## Create the Slack app

1. In Slack app management, choose **Create New App → From an app manifest**.
2. Paste [`manifest.yaml`](../manifests/slack/manifest.yaml) and install the app into a test workspace.
3. Under **Basic Information → App-Level Tokens**, create an app token with `connections:write`. Save the resulting `xapp-…` value locally as `SLACK_APP_TOKEN`.
4. Copy the bot token (`xoxb-…`) from **OAuth & Permissions** into `SLACK_BOT_TOKEN`.
5. Invite the MightShape bot to each channel where it should be used. The manifest deliberately omits `chat:write.public`.

The only bot scopes are:

- `commands` — receive `/design-think`;
- `chat:write` — publish and update the exercise thread;
- `files:write` — upload the generated PNG artifact.

There are no message-history or event-subscription scopes.

## Run locally with Socket Mode

From `collaboration-app/`:

```bash
cp .env.example .env
# Load the values from .env through your preferred local secret manager.
npm ci
npm run build
npm run start:slack
```

Required environment variables:

```text
SLACK_BOT_TOKEN=xoxb-…
SLACK_APP_TOKEN=xapp-…
```

For an honest offline smoke test, keep `DC_AI_MODE=mock`. It captures a source wall and explicitly says it has not performed semantic clustering. For live AI facilitation, set `DC_AI_MODE=openai` and provide `OPENAI_API_KEY`; the server sends only the bounded frozen workshop packet required for synthesis.

Do not commit `.env`, Slack tokens, or model-provider keys.

## Use it

1. In an invited channel, run `/design-think` or `/design-think How might we improve shift handoffs?`.
2. Choose an exercise and whether contributions should be open or sealed.
3. Teammates use **Add my input** on the root message. They can contribute more than once or explicitly choose **Pass this prompt**; passing never causes the facilitator to fabricate an answer for them.
4. The initiating member selects **Freeze & synthesize**. This closes collection, reveals a sealed set, and starts synthesis asynchronously.
5. Review the visible PNG and its text alternative in the same thread. Use **Close** when the exercise is finished, or **Delete workshop data** when the controller intends to remove the workshop and its recorded bot output.

## Operational limits

This local/single-process service uses the crash-safe file store. Configure the deployment scheduler to run `npm run purge-expired`; expiry removes local state but cannot call Slack to remove posts. Socket Mode is appropriate for controlled workspace use, but a production, multi-instance deployment should use a transactional `WorkshopStore`, managed secrets, operational monitoring, and an HTTPS deployment plan. The adapter deliberately does not claim enterprise retention, eDiscovery, DLP, confidentiality, or legal compliance. Channel members can see open inputs and any set revealed after freeze; use a channel appropriate for the exercise.
