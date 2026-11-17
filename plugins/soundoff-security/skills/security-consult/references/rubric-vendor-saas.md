# Rubric: vendor and SaaS

Status: DRAFT STUB. Starter questions only. When you use this rubric, apply the starter
questions and the six hard escalation triggers in SKILL.md, and say under Assumptions made
that this rubric is a draft with limited coverage.

Use this when a team wants to buy, trial or renew a vendor product, SaaS tool, browser
extension or outside service.

## Starter questions

1. What SoundOff data will the vendor store or see? In particular, is any of it FCI (agency
   quotes, orders, correspondence) or customer data? If yes and this is a new system, that
   is hard escalation trigger 5.
2. Does something already in the existing stack (see `soundoff-context.md`) do this job?
3. How do people sign in? Does it support single sign-on through Entra ID, or does it keep
   its own passwords?
4. What does it connect to? Does it need access to mailboxes, SharePoint, Azure, the
   network, or an account with admin or service-level rights (trigger 4)?
5. Is the vendor or its technology affected by a FAR 52.240-91 prohibition (Section 889,
   Kaspersky, covered apps, FASCSA), and does the contract carry any security terms such as
   those listed in trigger 6?

## Sections to draft

TODO (Bryan): draft the full rubric. Suggested headings:

- Data shared with the vendor and its classification
- Overlap with the existing stack
- Identity and access (Entra ID single sign-on, admin roles, offboarding)
- Integrations and permissions granted to the vendor
- Vendor security evidence and what SoundOff accepts
- Contract and procurement terms (FAR 52.240-91 prohibitions, scope-change clauses)
- Exit plan and data return or deletion
- Severity guidance and verdict examples
