import requests
from requests.auth import HTTPBasicAuth


class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def search_issues(self, jql: str, max_results: int = 50) -> list[dict]:
        """Fetch issues matching a JQL query."""
        url = f"{self.base_url}/rest/api/3/search/jql"
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": ["summary", "description", "issuetype", "status", "priority", "labels", "components"],
        }
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        response.raise_for_status()
        return response.json().get("issues", [])

    def assign_issue(self, issue_key: str, account_id: str) -> None:
        """Assign a JIRA issue to a user by account ID."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/assignee"
        payload = {"accountId": account_id}
        response = requests.put(url, headers=self.headers, auth=self.auth, json=payload)
        response.raise_for_status()

    def add_comment(self, issue_key: str, body: str) -> None:
        """Add a comment to a JIRA issue."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body}],
                    }
                ],
            }
        }
        response = requests.post(url, headers=self.headers, auth=self.auth, json=payload)
        response.raise_for_status()
