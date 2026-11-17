# soundoff-security

A voice of security you can bring into your own work. It reviews what you show it, tells you
what it sees in plain English, and ends with one clear verdict.

It advises. It never approves. Nothing this plugin says is a Cybersecurity sign-off.

## Who it is for

Any SoundOff Signal team that wants a security opinion early, before work is locked in:

- Software Engineering: designs, code changes, pull requests, CI/CD and agent workflows
- IT Development and Business Analysts: integrations, new tools, process changes that touch data
- Infrastructure: planned changes, before they go to change review
- Anyone weighing a new vendor, SaaS tool or AI use case

## How to invoke it

Install from the soundoff-approved marketplace:

    /plugin install soundoff-security@soundoff-approved

Then use it one of three ways:

1. Ask in plain language. "Can I get a security consult on this design?" Claude loads the
   skill when the request matches.
2. Run the skill directly: `/soundoff-security:security-consult` followed by what you want reviewed.
3. Use the subagent from a harness or another agent: `@agent-soundoff-security:security-reviewer`.
   This is the wrapper built for Software Engineering's harness. It can only read files in your
   repo. It cannot change anything.

Tell it who you are, what team you are on and what you want reviewed. If it needs something
to reach a verdict it will ask. Otherwise it states its assumptions and keeps going.

## What you get back

A plain-text summary you can paste straight into Jira or Teams:

    SECURITY CONSULT SUMMARY
    Team / requester:
    What was reviewed:
    Verdict:
    Findings:
    Conditions:
    Escalation trigger:
    Assumptions made:
    Advisory only. This is not a Cybersecurity approval.

Every consult ends in exactly one verdict:

- Proceed: nothing found that should slow you down.
- Proceed with conditions: go ahead once the listed conditions are met.
- Escalate to Cybersecurity: this needs a person on the Cybersecurity team. See below.

## What it will not do

- Approve anything, or stand in for a Cybersecurity review.
- Answer customer security questionnaires, SAM or Section 889 representations, or any other
  security attestation on SoundOff's behalf. It will not draft those answers either.
- Create tickets, send messages or contact anyone.
- Change your files. It has no write tools, no network access and no MCP servers.
- Tell your team how to build the fix. It describes the problem, the fix and the impact.
  The owning team decides how.
- Recommend blocking something without first asking who uses it and what it supports.

## How to escalate

When the verdict is Escalate to Cybersecurity:

1. Open a HelpDesk ticket in Jira, project ITHD.
2. Paste the full consult summary into the ticket.
3. Cybersecurity picks it up from there.

The plugin never opens the ticket for you. You can also open an ITHD ticket any time you
disagree with a verdict or want a person to look.

## What is in this version (0.1.0)

- Design and code rubric: fully drafted.
- Vendor and SaaS, AI use case, and infrastructure change rubrics: starter questions only.
  Consults in these areas still run and still apply the hard escalation triggers, but they
  say in the summary that the rubric is a draft.

## Feedback

Wrong verdict, confusing wording or a missing check? Open an ITHD ticket and mention
soundoff-security so Cybersecurity can add it to the eval cases in `evals/`.
