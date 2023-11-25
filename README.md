# Slack AI Bot

A slack GPT bot for summarizing conversations, creating JIRA tickets, etc.

1. Create Slack Bot

2. Set environment variables in `.env`

3. Run server with docker compose

``` sh
docker compose up -d prod --build
```

For debugging, please refer codes below

1. Run and attach to dev server

``` sh
docker compose up -d dev --build
docker attach slack_ai_dev
```
