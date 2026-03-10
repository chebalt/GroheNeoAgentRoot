import json

import anthropic
import yaml


def load_config(config_path: str) -> dict:
    """Load routing config from YAML."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _extract_text(issue: dict) -> str:
    """Extract searchable text from a JIRA issue (summary + description)."""
    summary = issue.get("fields", {}).get("summary", "") or ""
    description = issue.get("fields", {}).get("description")

    desc_text = ""
    if isinstance(description, dict):
        desc_text = _extract_adf_text(description)
    elif isinstance(description, str):
        desc_text = description

    issue_type = issue.get("fields", {}).get("issuetype", {}).get("name", "")
    labels = ", ".join(issue.get("fields", {}).get("labels", []))
    components = ", ".join(
        c.get("name", "") for c in issue.get("fields", {}).get("components", [])
    )

    parts = [f"Summary: {summary}"]
    if issue_type:
        parts.append(f"Type: {issue_type}")
    if labels:
        parts.append(f"Labels: {labels}")
    if components:
        parts.append(f"Components: {components}")
    if desc_text:
        parts.append(f"Description: {desc_text[:2000]}")

    return "\n".join(parts)


def _extract_adf_text(node: dict) -> str:
    """Recursively extract plain text from Atlassian Document Format."""
    if node.get("type") == "text":
        return node.get("text", "")
    parts = []
    for child in node.get("content", []):
        parts.append(_extract_adf_text(child))
    return " ".join(parts)


def _build_system_prompt(config: dict) -> str:
    """Build the system prompt from the routing config."""
    team = config.get("team", [])
    context = config.get("project_context", "")

    team_block = "\n".join(
        f"- **{m['name']}** (account_id: `{m['account_id']}`): {m['expertise']}"
        for m in team
    )

    return f"""You are a JIRA ticket routing assistant for the GROHE NEO project.

PROJECT CONTEXT:
{context}

TEAM MEMBERS AND THEIR EXPERTISE:
{team_block}

YOUR TASK:
Given a JIRA ticket, decide who should be assigned to it based on the ticket content and each team member's expertise.

RULES:
- You MUST respond with valid JSON only, no other text.
- The JSON must have exactly these fields:
  - "assignee_account_id": the account_id of the best-matching team member
  - "assignee_name": their name
  - "reason": one short sentence explaining why (this will be posted as a comment)
  - "confidence": "high", "medium", or "low"
- If you are unsure (confidence "low"), still pick the closest match.
- Never invent account IDs — only use the ones listed above."""


def route_issue(issue: dict, config: dict, api_key: str) -> dict | None:
    """Use Claude to decide who a ticket should be assigned to.

    Returns dict with assignee_account_id, assignee_name, reason, confidence
    or None if routing fails.
    """
    text = _extract_text(issue)
    system_prompt = _build_system_prompt(config)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Route this ticket:\n\nKey: {issue['key']}\n{text}",
            }
        ],
    )

    response_text = message.content[0].text.strip()

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response_text[start:end])
        else:
            print(f"  ERROR: Could not parse Claude response for {issue['key']}: {response_text}")
            return None

    # Validate the response has required fields
    required = {"assignee_account_id", "assignee_name", "reason", "confidence"}
    if not required.issubset(result.keys()):
        print(f"  ERROR: Missing fields in Claude response for {issue['key']}: {result}")
        return None

    # Validate account_id is from our team
    valid_ids = {m["account_id"] for m in config.get("team", [])}
    if result["assignee_account_id"] not in valid_ids:
        print(f"  ERROR: Claude returned unknown account_id for {issue['key']}: {result['assignee_account_id']}")
        return None

    return result
