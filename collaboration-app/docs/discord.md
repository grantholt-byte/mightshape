# MightShape for Discord

This optional 1.0.1 adapter turns one Discord channel into a structured MightShape workshop without reading ambient conversation. One member runs `/design-think start`; the app opens a setup modal, starts a public workshop card, and creates a public thread when the channel and permissions support it. Teammates contribute through buttons and private per-user modals. The initiator controls freeze, synthesis, and close. Forms use Discord's current Label-wrapped modal components instead of the deprecated Text Input-in-Action-Row layout.

## What it supports

- `/design-think start`, `/design-think status`, `/design-think retry`, and initiator-controlled `/design-think delete`
- protected sealed brainwriting as well as open mapping and prototyping exercises
- novice-assistive prompts explaining the immediate purpose and mindset
- per-user modal contributions, each labeled `USER_PROVIDED`
- a non-blocking **Pass** control so optional participation stays genuinely optional
- initiator-only freeze, retry, close, and delete controls enforced by the shared workshop core
- delivery-only retry from `REVIEW`; it reloads the immutable local artifact and never re-synthesizes
- source-linked whimsical affinity/process graphics uploaded as PNGs with attachment descriptions and text fallbacks
- thread-scoped activity when Discord can create a public thread; clean channel fallback otherwise
- signed HTTP interactions with prompt acknowledgement and asynchronous synthesis
- mention suppression on every posted or edited message

It intentionally uses no Gateway connection, requests no Gateway intents, and does not request Message Content. Ordinary channel messages are not workshop submissions. This avoids ambient surveillance and makes participation explicit.

## Discord setup

1. Create a Discord application in the [Developer Portal](https://discord.com/developers/applications).
2. In **General Information**, copy the Application ID and Public Key.
3. Create a bot token, store it only in your deployment secret manager, and never commit it.
4. Configure the Interactions Endpoint URL as `https://YOUR-HOST/interactions`. Discord must be able to reach it over HTTPS.
5. Configure Guild Install with the `applications.commands` and `bot` scopes. Request only View Channel, Send Messages, Attach Files, Create Public Threads, and Send Messages in Threads. The reviewable permission contract is in `manifests/discord/install.json`.
6. Copy `.env.example` to a local untracked environment file or configure the same variables in your host:

   ```text
   DISCORD_APPLICATION_ID=...
   DISCORD_PUBLIC_KEY=...
   DISCORD_BOT_TOKEN=...
   DISCORD_TEST_GUILD_ID=...   # optional; use during testing for immediate guild command updates
   DISCORD_PORT=3002
   ```

7. From `collaboration-app/`, install, build, and register the command:

   ```bash
   npm ci
   npm run build
   npm run register:discord
   npm run start:discord
   ```

When `DISCORD_TEST_GUILD_ID` is set, registration targets that test server. Without it, the command is registered globally and propagation can take longer. The script never prints the bot token.

For local testing, put an HTTPS tunnel in front of `localhost:3002` and point Discord at its `/interactions` URL. Do not treat a temporary tunnel as a production deployment.

## Facilitation modes

The default `DC_AI_MODE=mock` is an honest offline source wall: it preserves every note but does not pretend to semantically cluster it. Set `DC_AI_MODE=openai` and provide `OPENAI_API_KEY` to use live MightShape synthesis. The model receives only the frozen workshop record, treats every contribution as untrusted participant material, and returns conclusion-level artifacts rather than hidden reasoning.

## Data and security boundaries

- The single-process file store keeps records under `DC_TEAM_DATA_DIR` with owner-only permissions and a configurable retention date.
- The deployment scheduler should run `npm run purge-expired`; the command removes expired records and generated artifacts without calling Discord or a model provider.
- Raw Discord user, guild, channel, and interaction identifiers live only in the private adapter binding; portable project exports contain opaque participant IDs.
- Every mutating Discord interaction ID is hashed and durably claimed in the private workshop
  store for the record's full retention lifetime. The endpoint also rejects stale signed payloads.
  A process-local response cache can replay the exact acknowledgement, but correctness does not
  depend on that cache. Multi-instance hosting must replace the bundled file store with a transactional
  shared implementation before horizontal scaling.
- PNGs are uploaded directly to Discord as multipart attachments so they display in the workshop thread. Each includes an attachment description plus a text summary for accessibility and clients that suppress images.
- Buttons and modals mean the bot does not need to read channel history. Do not add Message Content merely for convenience.
- The app suppresses all allowed mentions, so participant text cannot ping `@everyone`, roles, or other users.
- Bot-post message and attachment IDs are held only in the private binding. Initiator deletion is best effort: confirmed bot posts are removed before local state; partial remote failures retain local state and retryable receipts, and the app never promises guaranteed confidentiality.

## Operational limits

This is an optional adapter, not a requirement for the Codex or Claude plugin. A public HTTPS host and Discord application registration are necessary. Thread creation is best effort because Discord channel types and server permissions vary. The single-process store is not suitable for horizontally scaled deployment until a transactional shared store and shared idempotency receipt store are configured.

Primary platform references: [Receiving and responding to interactions](https://docs.discord.com/developers/interactions/receiving-and-responding), [Application commands](https://docs.discord.com/developers/interactions/application-commands), [Message components](https://docs.discord.com/developers/components/reference), [Threads](https://docs.discord.com/developers/topics/threads), and [Permissions](https://docs.discord.com/developers/topics/permissions).
