# NEO Dev + QA Pipeline

You have been invoked as `/neo $ARGUMENTS`

`$ARGUMENTS` is the path to a markdown file containing the task to implement.

---

## Step 1 — Read the task file

Use the Read tool to read the file at: `$ARGUMENTS`

- If the path is relative, resolve it from `C:/projects/grohe/NEO/`.
- If the file does not exist, tell the user and stop immediately.
- Do not proceed until the file has been read successfully.

---

## Step 2 — Invoke the dev agent

Pass the full task content to the `grohe-neo-dev` agent using the Agent tool.

Do NOT implement anything yourself. Do NOT summarise or interpret the task — pass it verbatim.

Tell the dev agent to end its response with a **Handoff block** in this exact format:

```
## Handoff to QA

**Feature context:** <feature-doc-name(s), e.g. pdp, shopping-cart>
**Repos changed:** <list of repos>
**What was implemented:** <1–3 sentence summary>
**Key files changed:** <list of file paths>
**Known gaps or concerns:** <anything the QA agent should pay extra attention to, or "none">
```

---

## Step 3 — Invoke the QA agent

Once the dev agent has responded, extract the full Handoff block and pass it to the `neo-qa-engineer` agent using the Agent tool.

Pass the Handoff block verbatim — do not shorten or paraphrase it.

Also include the original task description so the QA agent has full context of what was requested.

---

## Step 4 — Report to the user

After the QA agent completes, output a final summary:

```
## Pipeline complete

### Implemented
<what the dev agent built — 2–4 bullet points>

### QA result: PASS / FAIL / PARTIAL
<test counts, new tests created, lint/type check results>

### Bugs found
<list with file + description, or "none">

### Next steps
<any bugs handed back to dev, or "ready to review / commit">
```
