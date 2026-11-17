# Rubric: design and code

Use this for designs, architectures, code changes, pull requests, repos, CI/CD pipelines and
AI agents built into software. Check the six hard escalation triggers in SKILL.md first.

## How to use this rubric

- Work through the eleven areas below. Skip an area only when it plainly does not apply, and
  say so under Assumptions made if the skip is a judgment call.
- If you have repo access, read the code and config. Do not ask the requester to describe
  something you can read.
- Each area lists what to check, what good looks like, when to raise a finding, why it
  matters and when it becomes an escalation.
- Write findings as problem, impact and fix. The owning team chooses the implementation.

## Severity guide

- High: on its own, this could plausibly expose customer agency data or FCI, let someone
  push or alter firmware, take over an account with broad access, or stop production.
- Medium: this weakens a protection. It would take a second failure to cause real harm, or
  the harm is limited to one internal system.
- Low: good hygiene that lowers future risk. Worth doing, not worth holding work for.

When unsure between two levels, pick the higher one if the cloud product platforms
(SoundOff Central, bluePRINT, ConnectNGo, SOC 3.0), FCI or customer data are involved.
Otherwise pick the lower one.

## 1. Identity and authentication (Entra ID)

Check:

- How do people sign in? How do services and jobs prove who they are to each other?
- Does sign-in go through Entra ID, or does the system keep its own user list and passwords?
- Is access granted by role or group, and is the default "no access"?
- Is there any shared login, built-in admin account or hard-coded bypass?
- Does anything grant more access than the task needs?

Good looks like: people sign in with their SoundOff identity through Entra ID, so
Conditional Access and MFA apply and access ends when someone leaves. Services use managed
or workload identities. Access is by role, with the fewest rights that do the job.

Raise a finding when:

- The system keeps its own passwords for employees when Entra ID sign-in is available: Medium.
  High if the system holds FCI, customer data or platform data.
- There is a shared account, default credential or auth bypass left in code: High.
- Every signed-in user gets the same broad access by default: Medium.
- Session or token lifetime is unlimited, or tokens are accepted without checking who issued
  them and who they are for: High on the cloud product platforms, otherwise Medium.

Why it matters: accounts that live outside Entra ID do not get turned off when someone
leaves and do not get MFA. One reused password can then open customer agency data, which is
a trust problem with public safety customers and a cost every employee-owner shares.

Escalate when: the change adds a new way to authenticate on a cloud product platform
(trigger 2), or needs a service account or privileged role (trigger 4).

Mapping: NIST CSF 2.0 PR.AA-01, PR.AA-03, PR.AA-05. ISO/IEC 27001:2022 A.8.26, A.8.27.

## 2. Secrets handling

Check:

- Are there passwords, keys, tokens, connection strings or certificates in source code,
  config files, sample files, test data, pipeline definitions, container images or commit
  history?
- Where do secrets live at run time, and who can read them?
- Can a secret be rotated without a code change? Has anything already exposed been rotated?
- Do logs, error messages or crash reports print secrets?

Good looks like: no secret is in the repo or its history. Secrets come from an approved
secret store at run time, are scoped to one service and can be rotated without redeploying.

Raise a finding when:

- A live secret is in the repo, the history or a pipeline definition: High. The fix always
  includes rotating it, because removing the line does not remove it from history.
- A secret is shared across environments or services: Medium.
- Secrets appear in logs or error output: Medium. High if those logs leave SoundOff.
- A placeholder or expired secret is in the repo: Low.

Why it matters: a secret in a repo is readable by everyone who can ever read that repo. If
it opens a platform database or a signing service, a single leaked file becomes a customer
data incident or a firmware integrity incident.

Escalate when: the secret belongs to a service account or privileged identity (trigger 4),
or it is a firmware signing key (trigger 2).

Mapping: NIST CSF 2.0 PR.AA-01. ISO/IEC 27001:2022 A.8.28.

## 3. Input validation (OWASP Top 10)

Check:

- Where does data enter from outside the trust boundary? Include web forms, API calls,
  uploaded files, device and vehicle telemetry, webhooks, and data pulled from other systems.
- Is input checked on the server, not only in the browser or app?
- Are database queries built with parameters, or by joining strings?
- Is output encoded for where it lands (HTML, SQL, shell, file path)?
- Does every request check that this user may act on this specific record, not only that
  they are signed in?
- Can a user make the server fetch a URL or open a file path of their choosing?
- Are uploads limited by type and size and stored away from executable paths?

Good looks like: the server treats everything from outside as untrusted, validates it
against what is expected, and checks authorization on each object. Framework protections
are left on.

Raise a finding when:

- Queries or commands are built from user input by string joining: High.
- A request can read or change another user's or agency's record by changing an ID: High.
- User-controlled content is rendered without encoding: Medium. High on a cloud product
  platform.
- The server will fetch arbitrary URLs or read arbitrary paths for a user: High.
- Validation exists only on the client: Medium.
- Error pages show stack traces or internal details to users: Low.

Why it matters: these are the most common ways real applications are breached. On the cloud
product platforms the result is one agency's data in someone else's hands, which is exactly
what public safety customers trust SoundOff to prevent.

Escalate when: fixing it requires a new internet-facing endpoint on a platform (trigger 2).
Otherwise these are normally conditions, not escalations.

Mapping: NIST CSF 2.0 PR.PS-06. ISO/IEC 27001:2022 A.8.28, A.8.29.

## 4. Dependency and supply chain risk

Check:

- What third-party packages, base images, build actions and SDKs does this add or update?
- Are versions pinned, with a lock file? Are build actions and base images pinned to a
  specific version or digest?
- Do they come from the official registry, and is each package the one intended (watch for
  look-alike names)?
- Is each one maintained, and does it have known vulnerabilities at the version used?
- Does any dependency run code at install or build time, or come from a prohibited source
  under FAR 52.240-91 (Section 889, Kaspersky, covered apps, FASCSA)?
- Who can publish to any internal registry or feed this build pulls from?

Good looks like: a short, deliberate list of dependencies, pinned and locked, from official
sources, with a known owner who updates them. Known-vulnerable versions are not shipped.

Raise a finding when:

- A dependency has a known vulnerability that is reachable in this use, at the version
  pinned: High if exploitable from outside, otherwise Medium.
- Versions float (no lock file, "latest" tags, unpinned build actions): Medium.
- A package is abandoned, has a single unknown maintainer and runs with broad access, or
  its name looks like a misspelling of a popular one: Medium. High if it runs in the build
  for a customer-facing system.
- A dependency adds much more capability than the feature needs: Low.

Do not recommend a new scanning product. Ask what the team already uses, and note that
Tenable is the vulnerability management tool in the existing stack.

Why it matters: a compromised package runs with the same access as SoundOff's own code. In a
pipeline that builds platform services or firmware, it can reach every agency and every
vehicle at once.

Escalate when: none of the six hard triggers is specific to dependencies. If a dependency
or its supplier appears to fall under a FAR 52.240-91 prohibition, raise it as a High
finding and make the condition that Cybersecurity confirms it through a HelpDesk ticket in
Jira ITHD before it is used. Do not decide yourself whether the prohibition applies.

Mapping: NIST CSF 2.0 GV.SC (category), ID.RA-01, PR.PS-02. ISO/IEC 27001:2022 A.8.28.

## 5. Multi-tenant isolation between agencies

Applies to anything on the cloud product platforms, or any system that holds data for more
than one customer.

Check:

- How does every query, cache entry, file path, message and background job know which agency
  it belongs to?
- Is the agency taken from the signed-in session on the server, or from something the client
  sends and could change?
- Is isolation enforced in one shared place, or does each developer have to remember it in
  each query?
- Can admin, support or reporting features see across agencies? Who can use them, and is
  that use logged?
- Do shared resources (caches, queues, search indexes, storage containers, exports) mix
  agencies?
- Are there tests that prove agency A cannot read or change agency B's data?

Good looks like: the tenant is set on the server from the authenticated identity and
enforced in one layer that every data path goes through. Cross-agency access is a named,
limited, logged capability. Isolation has automated tests.

Raise a finding when:

- A request can reach another agency's data by changing an identifier: High.
- Tenant filtering is done by hand in each query with no central enforcement: Medium. High
  if you find a path that misses it.
- A shared cache, index or export can return another agency's data: High.
- Cross-agency support access exists without logging or limits: Medium.
- There are no isolation tests: Medium.

Why it matters: agencies trust SoundOff with their fleet and operational data. One agency
seeing another's data is the kind of incident that ends up in procurement conversations
across Sourcewell, NASPO and GSA customers, and it hits every employee-owner.

Escalate when: the design adds a new store of customer data (trigger 5) or a new
cross-agency access path that needs privileged access (trigger 4).

Mapping: NIST CSF 2.0 PR.AA-05, PR.DS-01. ISO/IEC 27001:2022 A.8.27, A.8.29.

## 6. OTA firmware integrity

Applies to anything that builds, signs, stores, distributes or installs firmware, or that
changes how devices decide what firmware to trust.

Check:

- Is firmware signed, and does the device verify the signature before installing?
- Where is the signing key kept, who and what can use it, and is each use recorded?
- Can an older, vulnerable version be installed over a newer one?
- Is the update fetched over an authenticated, encrypted channel, and is the device talking
  to the real SoundOff service?
- Who can publish a firmware release, and does it take more than one person?
- What happens to a vehicle if an update fails partway? Can it recover?
- Can a release be targeted at the wrong agency or the wrong hardware?

Good looks like: every image is signed, devices refuse anything unsigned or older than what
they run, the signing key is held where no single developer or pipeline job can use it
unnoticed, releases need a second person, and a failed update leaves a working vehicle.

Raise a finding when:

- Devices install firmware without verifying a signature: High.
- The signing key is in a repo, a pipeline variable readable by many people, or on a
  developer machine: High.
- Rollback to older firmware is not prevented: Medium.
- One person can build, sign and publish a release alone: Medium. High if that path is
  reachable from a pipeline many people can change.
- A failed update can leave lights or sirens unusable: High. This is a safety issue, not
  only a security one. Say so plainly.

Why it matters: firmware runs on emergency vehicles in service. A bad or malicious update
is a public safety problem first and a company-ending trust problem second.

Escalate when: the change touches how firmware is distributed or signed on the cloud product
platforms. That is trigger 2 by definition. In practice most findings in this area travel
with an Escalate verdict.

Mapping: NIST CSF 2.0 ID.RA-09, PR.DS-02. ISO/IEC 27001:2022 A.8.27.

## 7. Public exposure behind Front Door WAF

Check:

- Is anything reachable from the internet that was not before? Include new hostnames, APIs,
  storage links, admin pages, test and staging sites, and webhooks.
- Does all public traffic come through Azure Front Door with the WAF on, or can the origin
  be reached directly?
- Is there an admin, debug, metrics or documentation endpoint on the public side?
- Is storage (blobs, file shares, buckets) public, or shared with long-lived links?
- Is TLS required end to end?
- Are there limits that stop one caller from flooding the service?

Good looks like: one public front door per service, behind Front Door WAF, with the origin
locked so it only accepts traffic from that front door. Admin and debug paths are not
public. Nothing is public by default.

Raise a finding when:

- An origin can be reached directly, bypassing Front Door WAF: High.
- An admin, debug or internal API is on the public internet: High.
- Storage holding FCI, customer data or platform data is public or uses links that never
  expire: High.
- A test or staging environment with real data is public: High. With fake data: Medium.
- No rate limiting on a public endpoint: Medium.

Before recommending that anything be closed or blocked, ask who uses it and what business
process it supports. A public link may be how a dealer or agency gets something they need.
The finding should carry a way to keep that process working.

Why it matters: public endpoints are scanned constantly. An exposed service that skips the
WAF is the shortest path from the internet to customer agency data, and an outage on the
platforms is downtime for the agencies that rely on them.

Escalate when: the change creates a new internet-facing exposure on a cloud product platform
(trigger 2) or needs a firewall rule exception (trigger 4).

Mapping: NIST CSF 2.0 PR.IR-01. ISO/IEC 27001:2022 A.8.26, A.8.27.

## 8. Logging of security-relevant events

Check:

- Does the system record sign-ins (success and failure), access denials, permission and role
  changes, admin actions, cross-agency access, data exports, firmware publishes and config
  changes?
- Does each record say who, what, when and from where?
- Can the people or services being logged change or delete the logs?
- Do the logs reach the place Cybersecurity monitors, or do they only sit on the server?
- Do logs contain secrets, full tokens or more personal or customer data than needed?
- Are clocks consistent so events can be lined up across systems?

Good looks like: the events above are recorded with who, what, when and where, cannot be
altered by the application's own users, are kept long enough to investigate, and are
available to the existing monitoring stack.

Raise a finding when:

- A system holding FCI, customer data or platform data records no sign-in or admin activity:
  High.
- Logs exist but only locally, where an attacker with access could erase them: Medium.
- Secrets or tokens are written to logs: Medium (see area 2).
- Events lack who or when, so they could not support an investigation: Medium.
- Logging is present but noisy or inconsistent: Low.

Do not recommend a new logging or monitoring product. XSIAM with Unit 42 MDR is the
monitoring stack. State the outcome ("these events are available to Cybersecurity
monitoring") and let the owning team and Cybersecurity work out how.

Why it matters: without these records nobody can tell a customer what happened, how much
data was touched or when it stopped. That turns a small incident into a long, expensive one
and makes honest answers to agencies impossible.

Escalate when: logging is not normally a trigger on its own. Escalate only if getting logs
out requires a firewall rule exception or service account (trigger 4).

Mapping: NIST CSF 2.0 PR.PS-04, DE.CM-09. ISO/IEC 27001:2022: no mapping within A.8.25 to
A.8.29.

## 9. Data classification (FCI and customer data)

Check:

- What data does this system create, store, process or pass along? Name it.
- Is any of it FCI (agency quotes, orders, correspondence)?
- Is any of it customer data (customer contracts, customer IP, documents customers shared
  with SoundOff, government-contract documents)?
- Is any of it platform data (customer agency data, vehicle telemetry)?
- Is it encrypted in transit and at rest?
- Where do copies end up: exports, reports, email, test environments, logs, backups,
  developer laptops, third-party services?
- Is real data used in development or test?
- How long is it kept, and can it be deleted when it should be?

Good looks like: the team can say what data the system holds and which category it is. It is
encrypted in transit and at rest, kept only where needed, and not copied into test systems,
logs or outside services.

Raise a finding when:

- FCI, customer data or platform data is stored or sent unencrypted: High.
- Real FCI, customer data or platform data is used in development or test, or sent to a
  third-party service not already in use for that purpose: High.
- The team cannot say what data the system holds: Medium. Ask, because the answer may
  change the verdict.
- Data is kept with no retention limit: Low. Medium if it is FCI or customer data.

Do not label anything CUI and do not apply CUI handling or CMMC language. SoundOff holds no
CUI. If the requester says a contract requires CUI handling, that is a scope change and
trigger 6.

Why it matters: FCI protection is a contractual duty under FAR 52.240-93. Customer data is
held on trust. Mishandling either one puts government sales channels and customer
relationships at risk, and both are what employee-owners depend on.

Escalate when: this is a new system that stores FCI or customer data (trigger 5). Ask early,
because this trigger is the one most often missed.

Mapping: NIST CSF 2.0 ID.AM-07, PR.DS-01, PR.DS-02. ISO/IEC 27001:2022 A.8.26.

## 10. Repo and CI/CD permissions

Principle: the fewest hands on repos that deploy to customer-facing systems.

Check:

- Who can write to this repo, and who can change its settings? Is that list as short as the
  work allows?
- Is the main branch protected? Does a change need review by someone other than its author?
- Who can change the pipeline definition, and does that change get the same review?
- What can the pipeline reach: which environments, which secrets, with what rights?
- Are production deployments gated by an approval, and are deploy credentials scoped to one
  environment?
- Can code from a fork, an outside contributor or an unreviewed branch run in a pipeline
  that has production secrets?
- Are personal access tokens or individual accounts used where a workload identity should be?

Good looks like: a short list of people with write access, a protected main branch with
review by a second person, pipeline changes reviewed like code, deploy credentials that are
short-lived and limited to one environment, and no path for unreviewed code to reach
production secrets.

Raise a finding when:

- One person can merge and deploy to a customer-facing system with no second person: High.
- Unreviewed code (fork, branch, pull request) can run with production secrets: High.
- Write or admin access is broad (whole department, stale accounts, former team members):
  Medium. High on a repo that deploys to a cloud product platform or builds firmware.
- Pipeline credentials are long-lived or have more rights than deployment needs: Medium.
- Deployments use an individual's personal token: Medium.
- Branch protection is on but admins bypass it routinely: Low.

Why it matters: whoever can change the repo or its pipeline can change what runs in front of
customers. Keeping that group small and every change reviewed is the cheapest protection
there is against both mistakes and a stolen account.

Escalate when: the fix or the design needs a service account, a privileged role or a
firewall rule exception (trigger 4).

Mapping: NIST CSF 2.0 PR.AA-05, PR.PS-06. ISO/IEC 27001:2022 A.8.25.

## 11. AI agent risks

Applies when an AI agent or model is part of the software or the delivery process: coding
agents, review bots, agents that call tools, or product features built on a model.

Check:

- What can the agent do? List its tools, the credentials it holds, the repos and systems it
  can reach, and whether it can write, deploy, send or delete.
- Does it have more access than a new team member would get for the same task?
- Do prompts, system instructions, config files or agent memory contain secrets?
- Does FCI, customer data or platform data go into prompts, and where does the model run?
- Can content the agent reads (a web page, a ticket, an email, a file in a repo, a customer
  upload) change what it does? Assume it can.
- Does agent output reach production without a person reviewing it? Include code, config,
  database changes, firmware and customer-facing text.
- Are the agent's actions logged so someone can see what it did and why?
- Is there a way to stop it quickly?

Good looks like: the agent has the least access that does the task, holds no long-lived
secrets, treats what it reads as untrusted, and cannot put anything into production without
a person reviewing and approving the change the same way they would for a colleague's work.
Its actions are logged.

Raise a finding when:

- Agent output can reach production, or a customer, with no human review: High.
- The agent holds production credentials, deploy rights or broad write access it does not
  need: High.
- Secrets are in prompts, instructions or agent config: High (see area 2; rotate them).
- FCI, customer data or platform data is sent to a model or service not already approved
  for that data: High.
- The agent acts on untrusted content with write or send tools and no approval step: High.
- The agent reads only, with scoped access, but its actions are not logged: Medium.
- Agent-written code is reviewed, but reviewers are not told it was agent-written: Low.

Why it matters: an agent with broad access acts faster than a person and does not know when
it has been tricked. Unreviewed agent output in a platform service or in firmware carries
the same public safety and customer trust risk as any other unreviewed change, at higher
speed.

Escalate when: the agent needs a service account or privileged access (trigger 4), touches
OTA firmware or adds an authentication path on a platform (trigger 2), or sends FCI or
customer data to a new system that will store it (trigger 5). For AI questions that are
about adopting a tool, not building one, also read `rubric-ai-use-case.md`.

Mapping: NIST CSF 2.0 PR.AA-05, PR.PS-06. ISO/IEC 27001:2022 A.8.25, A.8.28, A.8.29.

## Mapping summary

ISO/IEC 27001:2022 Annex A controls used above:

| Control | Title |
| --- | --- |
| A.8.25 | Secure development life cycle |
| A.8.26 | Application security requirements |
| A.8.27 | Secure system architecture and engineering principles |
| A.8.28 | Secure coding |
| A.8.29 | Security testing in development and acceptance |

NIST CSF 2.0 references used above: GV.SC, ID.AM-07, ID.RA-01, ID.RA-09, PR.AA-01, PR.AA-03,
PR.AA-05, PR.DS-01, PR.DS-02, PR.PS-02, PR.PS-04, PR.PS-06, PR.IR-01, DE.CM-09.

Mappings are for Cybersecurity's reference. Leave them out of the consult summary unless
the requester asks. NIST CSF 2.0 is the program's organizing framework, not a contractual
requirement, so never tell a team that CSF "requires" something.
