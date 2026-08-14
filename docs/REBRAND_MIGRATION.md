# Migrating from Design Council to MightShape

MightShape is the new product name. The methodology, ten fictional Council members, Inquiry
Lab, evidence rules, and portable project history continue unchanged.

## Release identity

The owner designated `1.0.1` as the coordinated rename and collaboration-source release. The
package identity changes even though project-state and evidence contracts remain backward
compatible.

OpenAI requires an update package to retain the existing listing's package name. Claude uses the
plugin name as the command namespace. Therefore MightShape must be installed and reviewed as a
new plugin identity; an in-place package rename would either fail validation or silently break
invocation expectations. The former OpenAI listing can be delisted after MightShape is approved
and published. Until then, avoid running both auto-discovered skills in the same session.

## What changes

- The visible product and marketplace name becomes **MightShape**.
- The primary explicit command remains `/design-think` where a host supports it.
- Codex uses `$design-think` (or the **Design Think** skill entry), ChatGPT uses
  `@design-think`, and the new Claude plugin uses `/mightshape:design-think`.
- New MightShape packages do not ship the old product-name invocation aliases.

## What intentionally stays stable

Existing project data remains under `.design-council/`. Do not rename that directory. It is a
versioned storage identifier, not current branding. The `DESIGN_COUNCIL` provenance value,
schema identifiers, `DC_*` environment variables, record IDs, consent versions, and stored
action identifiers also remain stable so existing projects, studies, exports, and audit trails
continue to validate.

Historical records can still contain the former product name. They should not be rewritten:
preserving what a released artifact or project state said at the time is part of historical
integrity.

## Moving an existing installation

1. Finish or export any active work and keep the `.design-council/` directory with the project.
2. Once MightShape is published, install it using the coordinates in the current platform
   installation guide.
3. Start a fresh host session and invoke the current entry point.
4. Open the existing project. Confirm its revision, current mode, evidence ledger, and Council
   memory are intact before removing the former plugin installation.
5. Remove the former plugin only through the host's documented uninstall flow.

Do not install both products as ambient auto-invoked skills during migration; duplicate routing
can make activation ambiguous. The old package name and repository path may remain visible in
historical release links, but they are not current product branding.
