# SoundOff Signal context

Read this before every consult. It is the source of truth for company facts, the security
stack, and what is in and out of compliance scope.

## Company

- SoundOff Signal is an employee-owned (ESOP) manufacturer of emergency vehicle lighting and
  sirens for police, fire and EMS. About 600 employees. Headquarters in Michigan.
- Corporate IT and manufacturing/OT share one campus. The two are physically segmented.
- Because the company is employee-owned, a serious incident lands on every employee-owner,
  not on outside shareholders.

## Customers

- Public safety agencies and government.
- Sold through GSA MAS, agency BPAs and cooperative purchasing vehicles (Sourcewell, NASPO).

## Cloud product platforms (top cyber risk)

- SoundOff Central, bluePRINT, ConnectNGo and SOC 3.0.
- Hosted on commercial Azure.
- They hold customer agency data and vehicle telemetry, and they deliver OTA firmware to
  vehicles in service.
- Treat any change to exposure, authentication or firmware delivery on these platforms as the
  highest-risk category. See hard escalation trigger 2 in SKILL.md.

## Teams

Use these names exactly:

- Software Engineering
- IT Development
- Business Analysts
- Infrastructure
- HelpDesk
- Cybersecurity

Never call Infrastructure "IT".

## Existing stack

Do not recommend a tool that duplicates one of these. If a consult needs a capability, first
ask whether something on this list already provides it.

- Network: Palo Alto firewalls managed in Strata Cloud Manager, Prisma Access
- Endpoint and detection: Cortex XDR, XSIAM with Unit 42 MDR
- Vulnerability management: Tenable
- Email security: Check Point
- Security awareness: KnowBe4
- Identity: Entra ID and on-prem Active Directory
- Productivity: Microsoft 365 (with Defender), SharePoint
- Cloud: Azure, with Front Door WAF in front of public endpoints
- Password management: Keeper
- Tickets and work tracking: Jira (HelpDesk project is ITHD)

## Compliance in scope

- NIST CSF 2.0 is the spine of the security program. It is the organizing framework. It is
  not a contractual requirement.
- FAR 52.240-93 (formerly 52.204-21): basic safeguarding of Federal Contract Information
  (FCI). 15 requirements.
- FAR 52.240-91: security prohibitions (Section 889, Kaspersky, covered apps, FASCSA).
- ISO/IEC 27001:2022: ISMS in progress, scoped to the cloud product platforms.
- NIST SP 800-53 Moderate: used as the control library for the cloud console. Do not
  conflate it with NIST SP 800-171. They are different documents with different purposes.
- PCI DSS: SAQ only.

## Out of scope

State this plainly whenever it comes up:

- SoundOff holds no CUI.
- SoundOff has no CMMC target.
- SoundOff has no SOC 2.

Do not apply CUI handling rules or CMMC language to SoundOff work. Doing so overprotects data
the company does not hold and sends teams chasing requirements that do not apply.

If a contract or request appears to change this (for example it contains DFARS 252.204-7021,
HSAR 3052.204-72, USPS-specific security terms or a written FedRAMP requirement), that is a
scope change. It is hard escalation trigger 6. Flag it. Never assume.

## Data terms used in consults

- FCI (Federal Contract Information): agency quotes, orders and correspondence.
- Customer data: customer contracts, customer IP, documents customers shared with SoundOff,
  and government-contract documents.
- Platform data: customer agency data and vehicle telemetry held in the cloud product
  platforms.

## Approved documents

Cite only documents listed in this table. If the table is empty, or nothing in it fits, cite
nothing. Never invent a policy name, document ID or section number, and never cite a document
from memory.

TODO (Bryan): fill in this table.

| Doc ID | Title | Use when |
| --- | --- | --- |
| TODO | TODO | TODO |
