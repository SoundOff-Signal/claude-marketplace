# Department profile: Cybersecurity

Read this only for documents owned by the Cybersecurity department. None of it
applies to other departments' documents.

## Identity

```yaml
department: Cybersecurity
owner: Cybersecurity                # or the owning role, e.g. Cybersecurity Architect
doc_id: SOS-ITCS-<type>-<SUBJECT>   # ITCS is Cybersecurity's code
classification: INTERNAL USE        # raise only when the content calls for it
```

The author is still the requester, not a fixed name.

## Frameworks and compliance

- **Program spine: NIST CSF 2.0.** Map controlled documents to CSF functions and
  categories in `nist_csf` (for example `GV.PO, PR.AA, DE.CM`). CSF organizes
  the program; it is not a contractual requirement, so never present it as one.
- **ISO/IEC 27001:2022.** For documents inside the ISMS scope (the cloud product
  platforms: SoundOff Central, bluePRINT, ConnectNGo), name the Annex A
  controls in `framework`.
- **Federal Contract Information.** SoundOff safeguards FCI under
  FAR 52.240-93 (formerly 52.204-21), whose 15 requirements are a subset of
  NIST SP 800-171. FAR 52.240-91 covers security prohibitions and exclusions.
- **NIST SP 800-53 Moderate** is the control library for the cloud console only.
  Do not conflate it with the 800-171 FCI baseline.
- **No CUI and no CMMC target.** Do not write CUI handling or CMMC obligations
  into a document. Flag these as scope changes to confirm, never assume them:
  DFARS 252.204-7021 on a DoD-funded order, HSAR 3052.204-72 in a DHS agreement,
  USPS-specific security terms, or a written FedRAMP requirement from an agency.
- **PCI DSS**: small footprint, SAQ only.

## Standing conventions

- Severity scale is **Critical / High / Medium / Low** everywhere. Do not add or
  rename levels.
- Incidents, exceptions, and risks are tracked in **Jira** (ITHD for tickets,
  RISK for the Risk Register, EDT for vulnerability work).
- **Changes affecting OT or production systems require OT asset-owner approval**
  and are scheduled around manufacturing continuity.
- Name the team, not "IT", when work belongs to another IT team
  (Infrastructure, HelpDesk, IT Development, Business Analysts).
- Remediation handoffs describe the problem, the fix, and its impact. How to
  apply the fix is the receiving team's call; leave out rollout steps.
- Cite documented records as sources, not individuals.
- Only approved documents are citable. Draft Confluence pages are not
  authoritative and do not go under Related Documents.

## Tooling to name correctly

- Palo Alto: firewalls (managed in Strata Cloud Manager), Cortex XDR, Prisma
  Access, Cortex XSIAM with Unit 42 MDR
- Vulnerability management: Tenable
- Email security: Check Point (a SaaS connector to Exchange Online, not an
  inline gateway)
- Phishing triage and awareness: KnowBe4 PhishER and KMSAT
- Identity: Microsoft Entra ID and on-prem Active Directory; ManageEngine
  ADAudit Plus for identity auditing
- Microsoft 365 (Defender for Endpoint and Office, Teams, SharePoint), Azure
  (commercial)
- Graylog for infrastructure logs (run by Infrastructure, separate from XSIAM)
- Corporate IT and OT/manufacturing share one campus with physical segmentation;
  IT-to-OT lateral movement belongs in scope statements.

## Boilerplate for controlled documents

These replace the generic blocks in `document-patterns.md`. Edit only the
`{{...}}` parts.

### Roles & Responsibilities

```markdown
| Role | Responsibility |
|---|---|
| President & CEO | Accepts Critical residual risk; declares a disaster and authorizes recovery spend. |
| VP of Information Technology | Executive Sponsor. Approves this document, resolves cross-functional conflict, and funds remediation. |
| Cybersecurity Architect | Document owner. Maintains the control set, reviews exceptions, reports posture, and leads incident response. |
| Infrastructure | Implements and operates the controls described here, maintains the underlying platforms, and responds to assigned tickets. |
| OT Asset Owners | Approve changes affecting production and manufacturing systems, and confirm maintenance windows. |
| Managers and Supervisors | Ensure their teams complete required training and follow this document; report suspected incidents promptly. |
| All Users | Follow this document, complete assigned security awareness training, and report suspected security events to the HelpDesk or Cybersecurity. |
```

### Exceptions

```markdown
Exceptions are requested in writing through a Jira ticket, and must state the
control not being met, the business justification, the compensating controls in
place, and a fixed expiration date. Cybersecurity reviews every request; the VP
of Information Technology approves exceptions carrying High residual risk, and
the President & CEO accepts Critical residual risk. Exceptions affecting
production or OT systems additionally require the approval of the responsible OT
asset owner. Approved exceptions expire automatically on the stated date and must
be re-requested; they are reviewed at least quarterly.
```

### Enforcement

```markdown
Compliance with this document is mandatory for all workforce members and third
parties acting on SoundOff Signal's behalf. Suspected violations are triaged by
Cybersecurity on the standard Critical / High / Medium / Low severity scale and
tracked in Jira. Confirmed violations are referred to the responsible manager
and, where warranted, to Human Resources for action under company policy, up to
and including termination of employment or contract. Attempts to bypass,
disable, or conceal the failure of a required control are treated as High
severity at minimum.
```

### Review Cycle

```markdown
This document is reviewed at least annually by the Cybersecurity Architect and
re-approved by the VP of Information Technology. An out-of-cycle review is
triggered by any of: a material change to the environment or supported
platforms, a Critical or High severity incident implicating the controls
described here, a change in contractual or regulatory obligation, an
organizational change altering the roles named above, or the retirement or
replacement of a named tool.
```

### Related Documents

```markdown
- SOS-ITCS-PY-IS Information Security Policy
- SOS-ITCS-PY-DC Data Classification Policy
- SOS-ITCS-PL-IR Incident Response Plan
- {{other approved sibling documents}}
- NIST Cybersecurity Framework (CSF) 2.0
- FAR 52.240-93, Basic Safeguarding of Covered Contractor Information Systems
- {{ISO/IEC 27001:2022 for ISMS-scope documents; NIST SP 800-53 Rev. 5 for cloud console documents}}
```

List only the approved sibling documents that actually apply, and keep the
framework references last.
