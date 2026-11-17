# Document patterns: structures and company-wide boilerplate

Pick the structure by what the document *is*, not what it is called. These are
company defaults for any department. If the requester's department has a
profile (see `departments/departments.yaml`), its boilerplate and section rules
take precedence over the generic blocks here.

Contents: Controlled documents · Working documents · Decks · Registers and
trackers · Generic boilerplate

## Controlled documents

Policies, standards, procedures, work instructions, plans, runbooks,
guidelines, and forms: documents that are approved, published, and revised.
Start from `assets/examples/controlled-document.md`.

Section order (a procedure or work instruction replaces Policy Statement with
numbered **Procedure** steps):

1. **Purpose**: why the document exists
2. **Scope**: people, sites, systems, products, or processes covered, and what is out of scope
3. **Definitions**: terms a reader outside the department needs
4. **Policy Statement** (or **Procedure**): the requirements or steps
5. **Roles & Responsibilities**: who does what
6. **Exceptions**: how exceptions are requested, approved, and expired
7. **Enforcement**: what happens when the document is not followed
8. **Related Documents**: approved sibling documents, then external standards
9. **Review Cycle**: cadence and what triggers an early review

Front matter: `doc_type`, `version`, `status`, `review_cycle`,
`version_history`, `approvals`, plus `doc_id` when the department has a code.
Write requirements as "must" statements a reader can act on, and keep the
document readable by people outside the department (HR, leadership, auditors).

Cite only approved documents under Related Documents. Drafts are not
authoritative, and citing them makes the reader chase something that may change.

## Working documents

Everything that is not approved and revised: reports, briefs, write-ups,
recommendations, investigation summaries, proposals, memos. **No** `status`,
`version_history`, `approvals`, or `review_cycle`: those signal an approval
process that did not happen. Use `layout: brief` for anything under about five
pages; a cover page on a two-page brief is wasted paper.

Typical shapes (adapt, do not force):

- **Report / brief**: Summary (the answer first) → Findings → Recommendations
  → Next Steps. Start from `assets/examples/report-brief.md`.
- **Recommendation / decision request**: The Ask → Background → Options (a
  table) → Recommendation → Cost and Impact → Decision Needed By.
- **Process or program write-up**: Overview → How It Works (a Mermaid flowchart
  earns its place here) → Inputs and Outputs → Roles → Metrics → Open Items.
- **Design or architecture write-up**: Summary → Current State → Proposed Design
  → Risks and Considerations → Impact on Operations → Rollout.
- **Handoff to another team**: what was found, why it matters, the fix, and the
  impact of applying it. Leave how to apply it to the receiving team.
- **Memo** (`layout: memo`): `to`, `from`, `cc`, `subject` in front matter; one
  topic; the action or decision in the first paragraph. Start from
  `assets/examples/memo.md`.

Write for the reader who will act on it. A non-technical reader needs the
decision and the one number that drives it, not pipeline caveats; put a chart
or table where it shows that quantity directly.

## Decks

Start from `assets/examples/deck.md`.

- One idea per slide; the `##` title states the point ("Three shows produced
  80% of leads"), not the topic ("Lead sources").
- Use the short lead-in line for the takeaway, then 3 to 7 bullets, one table,
  or one picture.
- Use `#` sections for a deck over about eight slides, and `=== CLOSING` at the
  end.
- Put talking points in speaker notes (`???`) rather than on the slide.
- Use visuals only where a point is hard to grasp without one.

## Registers and trackers

Start from `assets/examples/register.md`.

- One table per sheet; a short note line above it explains scoring or scope.
- Name status-like columns with the recognized names (Severity, Priority,
  Status, Risk Level, Rating, Result) so they get live colors and dropdowns.
- Calculate rather than type derived values: `=E{row}*F{row}` for a score,
  `=SUM(G{first}:G{prev})` for a total row.
- Put KPI tiles on a `[metrics]` sheet and the raw data on its own sheet.
- Registers are living files: no `status` or `version_history`.

## Generic boilerplate (company default)

Use these when the department has no profile. Replace every `{{...}}`;
`qa_check.py` fails on any that survive.

### Roles & Responsibilities

```markdown
| Role | Responsibility |
|---|---|
| {{Executive Sponsor title}} | Approves this document and resolves cross-functional conflict. |
| {{Document Owner title}} | Maintains this document, reviews exceptions, and reports on compliance. |
| Managers and Supervisors | Ensure their teams follow this document and raise issues promptly. |
| All covered employees | Follow this document and ask the document owner when it is unclear. |
```

Add a row only when the document genuinely introduces another actor.

### Exceptions

```markdown
Exceptions are requested in writing to the {{Document Owner title}} and must
state the requirement not being met, the business reason, any compensating
measures, and an expiration date. Approved exceptions expire on the stated date
and must be re-requested.
```

### Enforcement

```markdown
Compliance with this document is expected of everyone in scope. Suspected
violations are referred to the responsible manager and, where warranted, to
Human Resources for action under company policy.
```

### Review Cycle

```markdown
This document is reviewed at least {{annually}} by the {{Document Owner title}}
and re-approved by the {{Approver title}}, and sooner after a material change
to the process, organization, or obligations it covers.
```

### Document Control front matter

```yaml
version: "1.0"
status: draft
review_cycle: Annual
version_history:
  - version: "1.0"
    date: {{YYYY-MM-DD}}
    author: {{Author}}
    description: Initial release
    approved: Pending
approvals:
  - name: {{Approver name}}
    role: {{Approver title}}
    date: Pending
```
