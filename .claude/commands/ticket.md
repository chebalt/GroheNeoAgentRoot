# JIRA Ticket → Dev Agent

You have been invoked as `/ticket $ARGUMENTS`

`$ARGUMENTS` is a JIRA ticket key (e.g. `EDSD-2910`, `NEO-1234`).

---

## Step 1 — Fetch the ticket

Use the Atlassian MCP tool `mcp__atlassian__getJiraIssue` to fetch the ticket:

- **cloudId:** `4cf92fd2-4fc3-43dc-bda6-c6485e600138`
- **issueIdOrKey:** `$ARGUMENTS`
- **responseContentFormat:** `markdown`

If the ticket is not found, tell the user and stop.

---

## Step 2 — Fetch comments

Fetch the ticket again with `fields: ["comment"]` to get comments. The result may be large — if so, it will be saved to a file. Extract the last 3–5 comments (author, date, body text).

If extracting from a saved file, use Bash with a Python one-liner to parse the JSON and print the recent comments.

---

## Step 3 — Present the ticket summary

Display a concise summary to the user:

```
## <ticket-key>: <summary>

**Status:** <status> | **Assignee:** <assignee> | **Priority:** <priority>

### Description
<abbreviated description — key points and acceptance criteria only>

### Recent Comments
<last 3–5 comments with author and date>
```

---

## Step 4 — Ask the user what to do

Ask the user:

> What should the dev agent do with this ticket? You can:
> 1. Describe a specific task (e.g. "implement AC #4" or "fix the bug mentioned in the last comment")
> 2. Say "implement" to pass the full ticket to the dev agent
> 3. Say "skip" to stop here

---

## Step 5 — Invoke the dev agent

Once the user provides direction, pass the task to the `grohe-neo-dev` agent using the Agent tool.

Include in the prompt:
- The full ticket description and acceptance criteria
- The relevant comments
- The user's specific instructions
- The ticket key for branch naming

Tell the dev agent to end its response with a **Handoff block**:

```
## Handoff to QA

**Ticket:** <ticket-key>
**Feature context:** <feature-doc-name(s)>
**Repos changed:** <list of repos>
**What was implemented:** <1–3 sentence summary>
**Key files changed:** <list of file paths>
**Known gaps or concerns:** <anything the QA agent should pay extra attention to, or "none">
```

---

## Step 6 — Invoke the QA agent

Once the dev agent responds, extract the Handoff block and pass it (plus the original ticket description) to the `neo-qa-engineer` agent.

---

## Step 7 — Report

After the QA agent completes, output:

```
## Pipeline complete — <ticket-key>

### Implemented
<what the dev agent built — 2–4 bullet points>

### QA result: PASS / FAIL / PARTIAL
<test counts, new tests created, lint/type check results>

### Bugs found
<list or "none">

### Next steps
<any bugs handed back to dev, or "ready to review / commit">
```
