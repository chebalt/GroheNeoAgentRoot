# Ticket Router

Automated JIRA ticket routing bot for the NEO project. Reads unassigned tickets from a JIRA filter and assigns them to the appropriate person based on configurable routing rules.

## How It Works

1. Runs on a schedule via GitHub Actions (every 30 minutes)
2. Queries JIRA for unassigned tickets matching a JQL filter
3. Analyzes ticket summary and description against routing rules
4. Assigns the ticket to the correct person
5. Optionally adds a comment explaining the assignment

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### 3. Configure routing rules

Edit `config/routing_rules.yaml` to define your topic-to-assignee mapping.

### 4. Run locally

```bash
python -m ticket_router.main
```

## GitHub Actions

The bot runs automatically via `.github/workflows/ticket-router.yml`. Required repository secrets:

- `JIRA_BASE_URL` — e.g. `https://lixilg.atlassian.net`
- `JIRA_USER_EMAIL` — service account email
- `JIRA_API_TOKEN` — API token for the service account
