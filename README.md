# Slack AI Bot

A slack GPT bot for summarizing conversations, creating JIRA tickets, etc.

1. Create Slack Bot

2. Set environment variables in `.env`

3. Run server with docker compose

``` sh
docker compose up -d prod --build
```

4. Set request URL to Slack Bot ([Your app](https://api.slack.com/apps) - `Event Subscriptions`)

5. Add app to your channel and Request `@<app name>!summary` or `@<app name>!jira`


For debugging, please refer codes below

1. Run and attach to dev server

``` sh
docker compose up -d dev --build
docker attach slack_ai_dev
```
