# Third-party methodology and rights review

Maintainer document · last reviewed 2026-08-14 · excluded from generated plugin packages

This record supports source, trademark, and copyright review. It is not runtime guidance and is
not legal advice. Public availability is not the same as public-domain status or permission to
reuse protected expression.

## Distribution boundary

MightShape implements design thinking methods through independently authored prompts,
instructions, examples, schemas, and visuals. The runtime packages must not include or closely
adapt third-party course decks, worksheets, source cards, scripts, examples, illustrations,
diagrams, distinctive layouts, logos, or other brand assets. The MIT license applies only to
material the project has the right to distribute under MIT.

The package uses neutral lineage labels:

- `public_design_practice` for established methods described in public design sources;
- `supplemental_design_practice` for broader design, research, and experimentation practice;
- `mightshape_original` for mechanisms authored for this product.

Those labels do not imply a single origin or third-party approval.

## Stanford and d.school source review

The following sources informed the maintainer's historical and rights analysis; none is bundled
in the plugin:

1. [Stanford Name Use Guidelines](https://trademarks.stanford.edu/name-use-guidelines) — the
   university treats its name and unit names as marks and restricts third-party promotional use,
   particularly where affiliation or endorsement could be implied.
2. [Stanford Administrative Guide 1.5.4](https://adminguide.stanford.edu/chapters/guiding-policies-and-principles/conflict-interest/ownership-and-use-stanford-trademarks)
   and the [Stanford Identity Guide](https://identity.stanford.edu/visual-identity/stanford-logos/)
   — university marks, logos, emblems, and related imagery require authorized use and must not be
   combined with third-party branding or used to imply endorsement.
3. [Stanford d.school Design Thinking Bootleg](https://dschool.stanford.edu/tools/design-thinking-bootleg)
   — the current page identifies a Creative Commons Attribution-NonCommercial-ShareAlike 4.0
   International license. An older PDF used a 3.0 license; license terms are version-specific.
4. [Stanford d.school FAQ](https://dschool.stanford.edu/connect/faq) — describes noncommercial,
   share-alike, and attribution expectations for resource reuse and separately discusses its
   historic hexagon graphic.
5. Other linked d.school tools do not all carry identical terms. Treat each exact resource and
   version separately; do not infer that one tool's license covers another.

Implementation decision: institutional names are removed from marketplace copy, runtime skill
instructions, prompting, exercise steps, method-family labels, generated package copy, and product
graphics. The source references above remain here only for factual audit and counsel review.

## Copyright basis

The [U.S. Copyright Office's Circular 33](https://www.copyright.gov/circs/circ33.pdf) and
[copyright FAQ](https://www.copyright.gov/help/faq/faq-protect.html) explain that ideas, methods,
procedures, processes, and systems are not protected by copyright, while an author's particular
text, illustrations, examples, and other original expression may be protected.

Repository review compared the runtime method references against the principal cited source PDFs
using exact eight-word sequences and found no matches as of the review date. This is a useful
originality check, not a legal conclusion. Repeat it when method instructions materially change.

## Other trademark hygiene

- Use the generic term “sticky note,” not the 3M Post-it® brand, in runtime or promotional copy.
- Avoid third-party logos, institutional color systems, branded diagrams, and distinctive course
  layouts.
- A disclaimer does not grant rights or automatically cure confusing branding.

## Open product-name clearance issue

The former product name “Design Council” is also used by the long-established UK Design Council
in the design-methods, education, and innovation field. That overlap was not a finding of
infringement, but it created a material trademark-clearance question because the wording and
field were closely related. The product is being renamed MightShape; that candidate still
requires its own qualified legal review. Before relaunch or international marketplace expansion,
counsel should review federal, state, common-law, UK, EU, WIPO, marketplace, domain, and relevant
class records. Do not mark legal or trademark clearance complete until that review is documented.

## Release controls

- Run `python3 scripts/check_runtime_branding.py` after building packages.
- Keep this file outside `dist/openai/` and `dist/claude/`.
- Require source-and-rights review before incorporating any protected third-party expression.
- Obtain counsel review for the product name, final logo, and marketplace materials before claiming
  legal clearance.
