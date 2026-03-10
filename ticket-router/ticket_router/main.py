import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ticket_router.jira_client import JiraClient
from ticket_router.router import load_config, route_issue


def main() -> None:
    load_dotenv()

    base_url = os.environ["JIRA_BASE_URL"]
    email = os.environ["JIRA_USER_EMAIL"]
    api_token = os.environ["JIRA_API_TOKEN"]
    anthropic_key = os.environ["ANTHROPIC_API_KEY"]
    filter_id = os.environ.get("JIRA_FILTER_ID", "")
    jql = f"filter = {filter_id}" if filter_id else os.environ["JIRA_JQL_FILTER"]
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"

    config_path = Path(__file__).parent.parent / "config" / "routing_rules.yaml"
    config = load_config(str(config_path))

    if not config.get("team"):
        print("No team members configured. Edit config/routing_rules.yaml first.")
        sys.exit(0)

    client = JiraClient(base_url, email, api_token)

    print(f"Querying JIRA: {jql}")
    issues = client.search_issues(jql)
    print(f"Found {len(issues)} issue(s) from filter\n")

    routed = 0
    skipped = 0

    for issue in issues:
        key = issue["key"]
        summary = issue.get("fields", {}).get("summary", "")
        print(f"  [{key}] {summary}")

        result = route_issue(issue, config, anthropic_key)

        if result is None:
            print(f"    → SKIP (routing failed)\n")
            skipped += 1
            continue

        confidence = result["confidence"]
        assignee = result["assignee_name"]
        reason = result["reason"]

        if dry_run:
            print(f"    → [DRY RUN] Assign to {assignee} ({confidence} confidence)")
            print(f"    → Reason: {reason}\n")
        else:
            client.assign_issue(key, result["assignee_account_id"])
            comment = f"Auto-assigned to {assignee}: {reason}"
            client.add_comment(key, comment)
            print(f"    → ASSIGNED to {assignee} ({confidence} confidence)")
            print(f"    → Reason: {reason}\n")

        routed += 1

    print(f"Done. Routed: {routed}, Skipped: {skipped}")
    if dry_run:
        print("(DRY RUN mode — no changes were made. Set DRY_RUN=false to apply.)")


if __name__ == "__main__":
    main()
