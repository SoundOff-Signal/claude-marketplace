# Rubric: AI use case

Status: DRAFT STUB. Starter questions only. When you use this rubric, apply the starter
questions and the six hard escalation triggers in SKILL.md, and say under Assumptions made
that this rubric is a draft with limited coverage.

Use this when a team wants to use an AI tool, model, agent or MCP server in a business
process. For AI agents built into software or delivery pipelines, also read area 11 of
`rubric-design-code.md`.

## Starter questions

1. What business process is this for, who will use it, and what happens today without it?
2. What data goes into prompts, uploads or connected sources? Is any of it FCI, customer
   data or platform data, and where does the model run and keep that data?
3. What can the AI do besides answer? List anything it can read, change, send, buy or
   delete, and the accounts or permissions it uses to do so (service accounts and privileged
   access are trigger 4).
4. Does a person review the output before it reaches a customer, a production system, a
   contract or a government representation? AI must never answer a security questionnaire
   or attestation for SoundOff (trigger 1).
5. Does it connect to new outside services, plugins or MCP servers, and who controls what
   those can reach?

## Sections to draft

TODO (Bryan): draft the full rubric. Suggested headings:

- Use case and business owner
- Data going in and where it is processed and kept
- What the AI is allowed to do (tools, connectors, MCP servers, permissions)
- Human review of output
- Untrusted content and prompt injection
- Approved AI tools and how to request a new one
- Logging and the ability to turn it off
- Severity guidance and verdict examples
