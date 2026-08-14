# Design Council monetization recommendation

**Research checked:** August 13, 2026
**Status:** Product recommendation and pricing experiments, not approved pricing or a financial forecast.

## Recommendation

Keep **Design Council Core free** on Codex and Claude. Monetize the scarce, operational layer around it:

1. hosted Bring-Your-Own interviews;
2. access to qualified real participants through the future Design Council Exchange;
3. team governance, privacy, and deployment controls;
4. optional human research and facilitation services.

The strategic boundary is simple:

> Design Council Core provides intelligence. Design Council Exchange provides access to qualified
> human evidence.

Do not charge for better Council answers, core Design Thinking methods, project-state portability, the Evidence Firewall, or the right to reach a sound Build Gate decision. Those capabilities create trust, adoption, and differentiation. Charge when Design Council incurs real service costs or supplies scarce access, durable hosted operations, or organizational assurance.

This is a low-friction hybrid, not a crippled freemium prompt pack. A user should be able to install the plugin, complete a serious design journey, and export their work without creating a Design Council account or seeing an upgrade prompt. “Free” means no additional Design Council charge; users still need an eligible Codex/ChatGPT or Claude plan and remain responsible for their platform's model or usage costs.

The best near-term commercial sequence is: ship the free Core; run a small, manual, no-card hosted
interview pilot only after the participant-data hard stop below is satisfied; introduce pay-per-study
before a subscription; add subscription only when repeat use clears the stated threshold; and defer
credits until transaction volume makes ordinary pricing genuinely cumbersome.

## Why this boundary is defensible

### The instruction layer is abundant

A capable model can already perform portions of Design Thinking from a well-written prompt. Design Council must earn adoption through stronger outcomes: preserved evidence provenance, persistent Council identities, sealed divergence, longitudinal memory, appropriate reframing, and disciplined movement from uncertainty to learning. Paywalling those foundations would reduce the number of users who experience the product's differentiation.

The plugin also has little inherent marginal cost when it runs locally in the user's existing Codex or Claude environment. Charging for ordinary Council turns would therefore feel like metering the user's own model access rather than delivering a separate scarce service.

### Popular plugins monetize the service, not the install

A current sample of prominent Claude marketplace plugins shows a consistent pattern: the plugin
is a free client or connector, while the vendor monetizes an external service account, hosted
usage, collaboration, private data, or enterprise assurance. Claude's marketplace contract has
no native price or checkout field, and OpenAI currently prohibits plugin sales of digital
services. This is an observed sample and platform-contract inference—not proof that every plugin
uses the same model.

| Plugin example | Free plugin value | External commercial boundary |
|---|---|---|
| [Context7](https://claude.com/plugins/context7) | Live documentation access | [Private repositories, collaboration, usage and enterprise plans](https://context7.com/plans) |
| [Vercel](https://claude.com/plugins/vercel) | Work with authenticated projects, deployments and logs | [Hosted platform usage, Pro and Enterprise](https://vercel.com/pricing) |
| [Figma](https://claude.com/plugins/figma) | Work with authenticated design files and systems | [Paid seats and organization capabilities](https://www.figma.com/pricing-faq/) |
| [Sentry](https://claude.com/plugins/sentry) | MCP access is included even in its free Developer tier | [Team, Business and metered observability usage](https://sentry.io/pricing/) |
| [CodeRabbit](https://claude.com/plugins/coderabbit) | Listing explicitly describes the plugin as free | [Higher service levels and usage outside the plugin](https://www.coderabbit.ai/pricing) |
| [PostHog](https://claude.com/plugins/posthog) | Operate an authenticated PostHog account | [Metered hosted product usage after free allowances](https://posthog.com/pricing) |

The useful analogy for Design Council is not “sell a better prompt.” It is “make the free client
indispensable, then charge where a separate service delivers durable operations or scarce
access.”

### Research operations and participants are scarce

Hosted interviews create direct costs for model inference, storage, delivery, support, abuse prevention, and data handling. Recruiting qualified humans adds participant incentives, sourcing costs, screening, fraud risk, no-shows, and research operations. Current vendor pricing illustrates this distinction:

- Respondent prices recruitment by completed session, currently showing pay-as-you-go reference rates of **$40 for consumer sessions and $80 for B2B sessions**, with participant incentives charged separately. Its AI moderator and synthesis are included in the recruitment price. ([Respondent pricing](https://www.respondent.io/pricing))
- User Interviews currently shows **$49 and $98 pay-as-you-go session rates** for its two audience tiers and separately exposes higher-cost advanced B2B targeting. ([User Interviews pricing](https://www.userinterviews.com/pricing))
- Dovetail offers an individual free tier with one research project, then reserves scale, governance, access control, retention, and enterprise support for custom-priced enterprise use. ([Dovetail pricing](https://dovetail.com/pricing/))
- Context7 is a useful plugin-adjacent analogue: its basic utility is free, while private data, collaboration, higher usage, and enterprise controls are paid. ([Context7 plans](https://context7.com/plans))

These are market reference points, not direct comparables or evidence that Design Council can sustain the same prices.

## Current platform constraints

### OpenAI / Codex / ChatGPT

OpenAI's current **plugin** policy is stricter than ordinary external SaaS distribution. Plugins
may currently conduct commerce only for physical goods. They may not sell digital products or
services—including subscriptions, content, tokens, or credits—directly or indirectly through a
freemium upsell. A user may sign into an existing paid account and use an existing entitlement;
the plugin may explain why an entitlement is unavailable and link to an informational plan page,
but it may not initiate checkout, display subscription plans, promote an upgrade, or link directly
to an upgrade transaction. ([OpenAI plugin commerce policy](https://developers.openai.com/plugins/app-guidelines#commerce-and-monetization))

OpenAI's broader Apps SDK guidance says monetization details are still to come and discusses
connecting an app to an existing backend for sign-in or premium entitlements. That is useful
future direction, but it does not override the present plugin-directory policy.
([OpenAI Apps SDK guidance](https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk))

Therefore:

- do not make the business model depend on a future OpenAI revenue share or native checkout;
- keep the free local plugin independently useful;
- if a future OpenAI adapter recognizes an existing paid entitlement, keep acquisition and
  checkout outside the plugin and do not promote them in Council output;
- do not sell or promote Exchange credits, hosted-study subscriptions, or other digital services
  inside the OpenAI plugin under the current policy;
- recheck policy before adding any account or entitlement surface, even if the commercial service
  is operated separately;
- treat future Agentic Commerce support as an adapter, not a core dependency.

### Claude Code

Claude Code marketplaces provide discovery, Git/GitHub distribution, versioning, installation, and updates. The documented marketplace and plugin manifest fields do not describe a native paid-plugin checkout or revenue-share mechanism. That absence is an inference from the current documented contract, not a promise that Anthropic will never add commerce. ([Claude Code marketplace documentation](https://code.claude.com/docs/en/plugin-marketplaces))

Anthropic's current directory policy prohibits software that serves advertisements, sponsored
content, paid product placements, or is primarily promotional. It also prohibits software that
executes financial transactions without Anthropic's written permission and requires a clear
privacy policy for software that collects data or connects to a remote service.
([Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy))

Therefore:

- the Claude plugin must remain a real product rather than a funnel or advertisement;
- never insert sponsored recommendations into Council output;
- paid hosted capabilities must be optional and accurately described;
- account, privacy, and billing flows should live in the hosted service, not masquerade as native
  Claude marketplace billing;
- before connecting a hosted service to a Claude directory plugin, provide the required privacy
  link, verified support/contact route, controlled endpoints/domains, and a standard test account
  with representative sample data for review;
- obtain written clarification from Anthropic before adding any transaction flow inside Claude.

## Free and paid product boundary

| Surface | Recommended access | Rationale |
|---|---|---|
| Intake, stage orientation, and adaptive routing | Free | Core product value |
| Ten Council Human Models and Council panels | Free | Differentiation and trust |
| Sealed rounds, mutation, dissent, and Minority Report | Free | Methodological integrity |
| Evidence Firewall and project-state files | Free | Safety and portability |
| Reality Packets and synthetic participants | Free, using the user's platform capabilities | No separate scarce service by default |
| Interview guides, fieldwork kits, and Disclosure Guard | Free | Improves research quality and safety |
| Local visuals and exportable artifacts | Free | Avoid artifact lock-in |
| Hosted participant links and managed interview sessions | Introductory pilot, then paid outside the OpenAI plugin | Recurring compute, storage, delivery, and support |
| Managed transcript retention and cross-study workspace | Paid | Durable hosted operations and privacy obligations |
| Real-participant recruitment / Exchange | Usage-based paid | Scarce supply and direct participant costs |
| Verified practitioners and experts | Quoted or usage-based paid | High sourcing and verification cost |
| Team administration, RBAC, SSO/SCIM, audit logs, custom retention, DPA/SLA | Enterprise | Organizational assurance and operational cost |
| Facilitated workshops, study review, and research-ops help | Optional services | Human time, never required for self-service use |

## Low-friction customer experience

The free plugin should contain no routine upgrade banners, token meters, locked Council members, artificial wait states, or repeated calls to buy.

Outside the OpenAI plugin—or on a platform whose then-current policy permits the flow—ask for an
account only at an explicit service boundary, such as:

- “Create an interview link”;
- “Recruit five practitioners”;
- “Keep these interview sessions in a shared team workspace”; or
- “Apply our organization's retention policy.”

At that moment, explain the transition in one sentence: what leaves the local environment, why an
account is needed, what will be stored, and what it costs. Let the user cancel and continue with a
local fieldwork kit. In the OpenAI plugin, an unavailable entitlement may be explained only within
the current commerce policy; do not turn that explanation into an upgrade pitch.

Acquisition belongs outside both plugins: use an independent website, direct sales, or a separately
operated hosted-service flow. Do not put pricing, paid calls to action, checkout, or fake-door
upgrade experiments into Council output. The OpenAI adapter may recognize an entitlement the user
already has and explain an unavailable one neutrally; that is not permission to market the upgrade.

Prefer value-first sampling:

- allow a first small hosted study without a card;
- show the External Study Packet and Disclosure Guard result before upload;
- charge for completed or intentionally reserved service, not failed sessions;
- make export and deletion straightforward;
- never hold the canonical local project state hostage to a subscription.

## Pricing hypotheses to test

The following numbers are **experiments**, not settled prices. Each should be tested with customer
interviews, off-plugin fake-door research, concierge pilots, willingness-to-pay conversations, and
real cost data before implementation. No fake-door offer belongs inside the OpenAI or Claude plugin.

### Experiment A — hosted Bring-Your-Own interviews

- Trial: first study with up to 5 completed text interviews, no card.
- Pay per study: **$19** for up to 20 completed text interviews within a defined retention window.
- Solo subscription: **$29/month** for approximately 100 completed text interviews, study history, and standard exports.
- Team workspace: **$99/workspace/month** for shared studies, permissions, and pooled usage; avoid per-seat pricing initially because collaboration should not be penalized.
- Overage: price only after observing real inference, support, storage, and payment costs; warn before charging.

Before any customer-facing offer, define interview duration/turn limits, model tier, retention and
deletion window, storage/export scope, team allowance, overage behavior, and support response. The
numbers above are not sufficiently specified to quote yet.

Test the pay-per-study offer against the subscription. Occasional discovery work may fit transactional pricing better than another recurring subscription.

### Experiment B — Exchange recruitment

Do not build an owned participant panel first. Start with a concierge or partner-backed beta and show participant incentives separately.

Two pricing structures are worth testing:

1. **Transparent pass-through:** participant incentives plus documented external sourcing,
   screening, verification, and payout costs, with a **15–25% orchestration fee** applied to that
   disclosed cost base.
2. **Per-completed-session fee:** an experimental **$20–45 platform fee for general consumers** or **$50–100 for professional/B2B participants**, plus the participant incentive.

Use the higher of actual cost coverage or the tested customer price. Do not promise these ranges until completion rates, screening effort, fraud loss, refunds, and support load are known. Expert and rare-role research should be quoted rather than forced into a flat rate.

Future `EXCHANGE_CREDITS` may simplify purchasing and participant compensation in a separately
operated service where platform policy permits it. They should be ordinary platform credits with
a clear currency value, refund rules, expiration policy, and ledger—not crypto, speculation, or an
obscured fee. Do not expose, sell, or promote those credits in the OpenAI plugin under the current
commerce policy.

### Experiment C — enterprise

Use annual custom contracts after repeated demand for:

- SSO/SCIM and role-based access;
- audit logs and configurable retention/deletion;
- data residency or private deployment;
- security review, DPA, SLA, and procurement support;
- verified confidential participant networks;
- consolidated usage and billing.

Do not prebuild these controls merely to justify a tier. Price from implementation/support cost and customer value after design-partner discovery.

### Experiment D — optional human services

Possible validation ranges:

- study-plan or synthesis review: **$750–$1,500**;
- facilitated Design Council workshop: **$2,500–$5,000**;
- custom research program: scoped proposal.

Every services quote must state the concrete deliverables, revision boundary, participant or
workshop scope, schedule, data handling, and what implementation is excluded.

Services can finance early learning but should be standardized over time so the product does not become a consulting business disguised as software.

## Unit economics framework

Track economics at the study and completed-session level before setting public prices.

### Hosted Bring-Your-Own study

```text
contribution_margin_per_study =
  study_revenue
  - model_inference
  - hosting_and_storage
  - email_or_message_delivery
  - payment_processing
  - expected_support_and_refunds
  - abuse_and_moderation_cost
```

Measure:

- completed sessions per study;
- model and tool cost per completed session;
- transcript/storage cost by retention period;
- support minutes per study;
- failed-session and refund rate;
- gross margin before and after support;
- conversion after the free study;
- 30-, 60-, and 90-day repeat-study rates.

### Exchange session

```text
contribution_margin_per_completed_session =
  researcher_fee
  - participant_incentive
  - sourcing_or_partner_cost
  - screening_and_verification
  - interviewing_and_synthesis_compute
  - payout_and_payment_fees
  - fraud_no_show_and_refund_reserve
  - participant_and_researcher_support
```

Also track:

- qualified-match rate;
- invite-to-completion rate;
- median time to first completion;
- participant replacement rate;
- evidence usefulness rated before synthesis is revealed;
- participant experience and opt-out rate;
- contradiction rate between synthetic hypotheses and human evidence;
- concentration risk by participant supplier.

The goal is not to maximize gross margin by underpaying participants. Incentives should reflect time, scarcity, expertise, and burden. Research quality and participant trust are product inputs, not costs to squeeze indiscriminately.

## Staged path

### Stage 0 — free public core

- Ship and validate the local plugin on both platforms.
- Collect optional, content-free demand signals such as `external_participant_needed` and `bring_your_own_study_created`.
- Measure repeat use and outcome quality; do not infer willingness to pay from installs.

### Stage 1 — hosted Bring-Your-Own private beta, outside the OpenAI plugin

- Add authentication only to the hosted interview service.
- **Hard stop before any real participant data:** publish deployment-specific privacy and terms,
  define retention/deletion and subprocessors, establish a monitored support/security route, and
  verify consent and incident-response operations. Until then, use fictional test data only.
- Offer the first small study free.
- Validate consent, deletion, Disclosure Guard, retention, support load, and actual per-session costs.
- Test pay-per-study versus subscription with real purchase intent.

### Stage 2 — paid Bring-Your-Own, outside the OpenAI plugin

- Launch the winning pricing form with clear limits and exports.
- Add team workspaces only after multiple collaborators use the same studies.
- Keep local Inquiry Lab and fieldwork kits fully functional for non-paying users.

### Stage 3 — Exchange concierge beta

- Fulfill a narrow set of participant requests manually or through an established provider.
- Price incentives separately and disclose what is verified versus self-reported.
- Learn screening, fraud, replacement, and support economics before automating matching.

### Stage 4 — Exchange provider and enterprise

- Implement the existing participant-source provider contract behind Inquiry Lab.
- Add credit accounting only when usage volume makes ordinary per-study checkout cumbersome.
- Build enterprise controls in response to signed design-partner requirements.

## Privacy and trust boundaries

Monetization must not create an incentive to exploit project or participant data.

- Local by default: core project state remains in the user's environment unless they explicitly invoke a hosted capability.
- Minimum disclosure: upload the approved `ExternalStudyPacket`, never the private `InternalStudy` by default.
- Solution Blackout and exposure level remain methodological controls, not paid features.
- Separate billing identity, researcher account, participant identity, matching profile, and researcher-visible profile.
- Project-owner consent never substitutes for participant consent.
- Do not use raw project content, source code, transcripts, or participant quotations for model training or product analytics by default.
- Collect product analytics only as optional, minimized events without project content.
- Publish retention, deletion, subprocessors, incident response, and model-provider behavior before accepting hosted interview data.
- Never promise anonymity, confidentiality, credential verification, legal conflict screening, or HIPAA readiness until the relevant controls and agreements actually exist.
- Do not sell confidential project content or participant data.

OpenAI currently requires personal-data processing to be necessary, user-authorized, legally disclosed, and minimized; its App Developer Terms also prohibit app processing of PHI and PCI-regulated payment-card data. Those constraints reinforce using a payment provider and keeping sensitive study categories out of the hosted beta until separately reviewed. ([OpenAI App Developer Terms](https://openai.com/policies/developer-apps-terms/))

## What not to monetize

Do not monetize:

- individual Council members or “premium personalities”;
- deeper reasoning or a less-safe evidence policy;
- Minority Reports, dissent, or knowledge boundaries;
- the Evidence Firewall, consent guidance, Disclosure Guard, or Reality Check;
- local state import/export or history recovery;
- basic visuals, templates, or core methods;
- access to one's own research data;
- hidden sponsored tools, methods, experts, or participant recommendations;
- user project data, participant data, or training rights;
- artificial token bundles for ordinary local plugin use.

Charging for safety, rigor, or export would make the free version methodologically worse. Sponsored answers would also conflict with the Council's epistemic independence and Anthropic's directory policy.

## Decision triggers

Treat these as pre-committed learning thresholds, not promises to investors or publication claims.

### Start hosted beta when

- the core plugin demonstrates non-inferior outcome quality against a competent Design Thinking prompt;
- at least 20 target users have asked for external participant links or completed a local fieldwork workflow;
- consent, deletion, External Study Packet, and Disclosure Guard paths pass adversarial review;
- cost can be measured per completed session.

### Turn on payment when

- at least 10 beta users complete a hosted study;
- at least 5 independently express purchase intent at a specific tested price;
- at least 25% of beta study creators start a second study within 60 days, or interviews establish a credible episodic pay-per-study market;
- support-inclusive contribution margin is positive at the tested price;
- the payment and privacy flows pass platform-policy review.

### Favor subscription when

- repeat users run at least two studies in a typical month;
- recurring retention is stronger than one-off demand;
- a subscription reduces purchasing friction rather than manufacturing lock-in.

Otherwise favor pay per study.

### Start Exchange concierge when

- there are at least 25 qualified recruitment requests in a narrow audience category;
- at least 10 requesters accept a tested fee and incentive range;
- a supplier or manual process can meet a stated completion and replacement standard;
- participant consent, screening labels, and evidence provenance are operationally reliable.

### Build an owned network when

- partner economics or quality repeatedly fail despite meaningful volume;
- repeat demand is concentrated in participant groups Design Council can recruit and retain responsibly;
- the expected margin justifies verification, fraud, payout, support, and marketplace-liquidity costs.

Do not build an owned network merely because the Exchange architecture exists.

### Add enterprise controls when

- at least five credible organizations request the same control;
- at least two are willing to enter a paid design-partner agreement;
- the control is an organizational requirement, not a workaround for a weak core product.

## Bottom line

Launch Design Council as a generous, trustworthy free plugin. Let its methodological quality create reach and credibility. Introduce payment only where the product crosses from intelligence into operations or scarce human access.

The cleanest initial business is:

```text
FREE CORE
  local Design Council + Inquiry Lab + evidence discipline

OPTIONAL HOSTED SERVICE
  Bring-Your-Own interview links + managed sessions

USAGE-BASED REALITY LAYER
  Exchange recruitment + incentives + verification where real

ENTERPRISE
  governance + privacy controls + deployment assurance
```

This model preserves a seamless first experience, aligns revenue with real delivered value, is
compatible with current platform rails despite the absence of native paid-plugin checkout, and
leaves room for platform commerce adapters if OpenAI or Anthropic add them later.
