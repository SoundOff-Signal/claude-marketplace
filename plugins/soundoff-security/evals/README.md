# Evals

These cases check that the plugin gives the answer Cybersecurity would give. Each case is a
real or realistic request, the verdict it should get, and Bryan's own answer to compare
against.

## Case format

One markdown file per case in `cases/`. Copy `cases/_template.md` and fill in every section.

| Section | What goes in it |
| --- | --- |
| Scenario | The request, written the way the requester would phrase it. Keep their words, their level of detail and whatever they left out. Do not tidy it into security language. |
| Expected verdict | Exactly one of: Proceed, Proceed with conditions, Escalate to Cybersecurity. |
| Triggers that should fire | The hard escalation trigger numbers (1 to 6) from SKILL.md that apply, or "None". |
| My actual answer | What Bryan actually told the requester, or would tell them. This is the reference answer. |
| Pass criteria | What the plugin's output must contain or avoid to pass. Write these so someone else could grade the case without asking. |

## How to run a case

1. Start a fresh session with the plugin enabled.
2. Paste the Scenario text as the request. Add nothing else.
3. Compare the consult summary to the case:
   - Verdict matches Expected verdict.
   - Every trigger listed fired, and no others did.
   - Every pass criterion is met.
   - The summary uses the exact plain-text output format and ends with the advisory line.
4. If the output differs from My actual answer in a way that matters, fix the skill or the
   rubric, not the case, unless the case itself was wrong.

A case passes only when the verdict, the triggers and every pass criterion match.

## Notes

- These are human-graded cases. They are not yet in the layout that `claude plugin eval`
  runs automatically.
- Do not put real customer names, agency names, credentials or contract text in a case.
  Rewrite the scenario so the security question stays the same and the identifying details
  are gone.

## Cases

| File | Status |
| --- | --- |
| `cases/voice-kiosk-design.md` | Empty, to be written |
| `cases/graylog-mcp-approval.md` | Empty, to be written |
| `cases/dev-registry-decryption-exclusions.md` | Empty, to be written |
| `cases/project-sentry.md` | Empty, to be written |
