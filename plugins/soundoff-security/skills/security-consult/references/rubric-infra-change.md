# Rubric: infrastructure change

Status: DRAFT STUB. Starter questions only. When you use this rubric, apply the starter
questions and the six hard escalation triggers in SKILL.md, and say under Assumptions made
that this rubric is a draft with limited coverage.

Use this when a team plans a network, firewall, server, cloud resource, identity or endpoint
change. The team that owns most of these changes is Infrastructure. Never call it "IT".

## Starter questions

1. What is changing, who uses the thing being changed, and what business process does it
   support? Ask this before suggesting that anything be blocked, closed or removed.
2. Does the change touch the production floor, SMT line, PLCs or production VLANs, or let
   traffic pass between corporate and production networks? If yes, that is hard escalation
   trigger 3.
3. Does it need privileged access, a service account or a firewall rule exception? If yes,
   that is trigger 4.
4. Does it make anything newly reachable from the internet, or change how people or systems
   authenticate? On the cloud product platforms that is trigger 2.
5. If the change goes wrong, what stops working, for whom, and how is it rolled back?

## Sections to draft

TODO (Bryan): draft the full rubric. Suggested headings:

- What is changing and who depends on it
- IT/OT boundary and segmentation
- Network exposure and firewall policy
- Identity, privileged access and service accounts
- Cloud resources in Azure
- Monitoring and logging coverage after the change
- Rollback and production downtime risk
- Severity guidance and verdict examples
