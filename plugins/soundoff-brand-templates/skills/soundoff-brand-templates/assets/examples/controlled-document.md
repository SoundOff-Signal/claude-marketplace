---
title: "{{Document Title}}"
subtitle: "{{One-line description}}"
doc_type: Policy                    # Policy | Standard | Procedure | Work Instruction | Plan | Guideline
doc_id: "{{SOS-<dept code>-PY-<SUBJECT>, or delete this line if the department has no code}}"
department: "{{Requester's department}}"
owner: "{{Owning role, e.g. Director of Quality}}"
author: "{{Requester's name and title}}"
version: "1.0"
status: draft
review_cycle: Annual
classification: INTERNAL USE
version_history:
  - version: "1.0"
    date: "{{YYYY-MM-DD}}"
    author: "{{Author}}"
    description: Initial release
    approved: Pending
approvals:
  - name: "{{Approver name}}"
    role: "{{Approver title}}"
    date: Pending
---

<!-- Controlled-document skeleton. Replace every {{...}}; qa_check.py fails on
     any that survive. If the department has a profile in
     references/departments/, its boilerplate replaces the generic blocks below. -->

# Purpose

{{Why this document exists and what it protects or standardizes.}}

# Scope

{{Who and what this applies to: people, sites, systems, products, processes.
Say what is out of scope when that is likely to be asked.}}

# Definitions

| Term | Definition |
|---|---|
| {{Term}} | {{Plain-language definition}} |

# Policy Statement

{{The requirements, written as "must" statements a reader can act on. For a
procedure, use numbered steps instead and title this section "Procedure".}}

# Roles & Responsibilities

| Role | Responsibility |
|---|---|
| {{Executive Sponsor title}} | Approves this document and resolves cross-functional conflict. |
| {{Document Owner title}} | Maintains this document, reviews exceptions, and reports on compliance. |
| Managers and Supervisors | Ensure their teams follow this document and raise issues promptly. |
| All covered employees | Follow this document and ask the document owner when it is unclear. |

# Exceptions

Exceptions are requested in writing to the {{Document Owner title}} and must
state the requirement not being met, the business reason, any compensating
measures, and an expiration date. Approved exceptions expire on the stated date
and must be re-requested.

# Enforcement

Compliance with this document is expected of everyone in scope. Suspected
violations are referred to the responsible manager and, where warranted, to
Human Resources for action under company policy.

# Related Documents

- {{Approved sibling documents, by ID and title}}

# Review Cycle

This document is reviewed at least {{annually}} by the {{Document Owner title}}
and re-approved by the {{Approver title}}, and sooner after a material change
to the process, organization, or obligations it covers.
