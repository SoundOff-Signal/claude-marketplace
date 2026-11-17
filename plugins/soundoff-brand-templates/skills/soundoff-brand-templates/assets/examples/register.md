---
# Example values: replace author, department, people, and dates with the requester's.
title: Corrective Action Tracker
subtitle: Open and recently closed corrective actions
doc_type: Register
department: Quality
author: Sam Rivera, Supplier Quality Engineer
date: 2026-11-17
classification: INTERNAL USE
---

## Scoreboard [metrics]

| Metric | Value | Target | Context |
|---|---|---|---|
| Open actions | 4 | 3 or fewer | lower is better |
| On-time closure | 86% | 90% | higher is better |
| Avg days open | 21 | 30 | lower is better |

## Actions

Likelihood and Impact are scored 1 to 5; Score is calculated.

| ID | Issue | Owner | Opened | Likelihood | Impact | Score | Severity | Status |
|---|---|---|---|--:|--:|--:|---|---|
| CA-101 | Connector pin plating thin | Supplier Quality | 2026-09-02 | 4 | 4 | =E{row}*F{row} | High | In Progress |
| CA-102 | Label misprint on carton | Packaging | 2026-09-15 | 2 | 2 | =E{row}*F{row} | Low | Closed |
| CA-103 | Solder void rate above limit | Production | 2026-10-01 | 3 | 5 | =E{row}*F{row} | Critical | Open |
| CA-104 | Late inspection records | Receiving | 2026-10-20 | 3 | 2 | =E{row}*F{row} | Medium | Not Started |
| Total |  |  |  |  |  | =SUM(G{first}:G{prev}) |  |  |
