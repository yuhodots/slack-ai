import os
import time
import json
from loguru import logger
from collections import defaultdict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
from slack_ai.prompts import ACTION_LIST, jira_ticket, summary
from openai import OpenAI


# load environment variables
load_dotenv()

# set openai client
openai_client = OpenAI()

# set slack client
rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=1)
signature_verifier = SignatureVerifier(signing_secret=os.environ["SLACK_SIGNING_SECRET"])
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
slack_client.retry_handlers.append(rate_limit_handler)
thread_ts2pids = defaultdict(list)

# run fastapi
app = FastAPI()


def format_message(channel, raw_message):
    return {
        "channel": channel,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": raw_message,
                },
            }
        ],
    }


def process_slack_events(body, headers):
    # Avoid replay attacks
    if abs(time.time() - int(headers.get("X-Slack-Request-Timestamp"))) > 60 * 5:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    if not signature_verifier.is_valid(
        body=body, timestamp=headers.get("X-Slack-Request-Timestamp"), signature=headers.get("X-Slack-Signature")
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = json.loads(body)
    return data


def get_action(user_message, slack_bot_id):
    user_message = user_message.replace(f"<@{slack_bot_id}>", "").strip()

    # select action
    if user_message.startswith("!"):
        action = user_message[1:]
        if action not in ACTION_LIST:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
        return user_message, action
    else:
        return user_message, None


def process_conversation(messages):
    conversation = []
    for message in messages:
        conversation += f"[{message['user']}]: "
        conversation += message["text"]
        if "files" in message:
            for file in message["files"]:
                conversation += f"<File: {file['mimetype']}>"
    return "\n".join(conversation)


def run_openai_api(prompt, model="gpt-4"):
    completion = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt['system']},
            {"role": "user", "content": prompt['user']}
        ]
    )
    return completion


def run_slack_ai(action, channel, ts):
    logger.info(f"action: {action}, channel: {channel}, ts: {ts}")
    slack_messages = slack_client.conversations_replies(channel=channel, ts=ts)["messages"]
    conversation = process_conversation(slack_messages)
    template_func = jira_ticket if action == "jira_ticket" else summary
    prompt = template_func.template(conversation)
    gpt_response = run_openai_api(prompt)
    formatted_reply = format_message(channel, gpt_response['choices'][0]['message']['content'])
    slack_client.chat_postMessage(**formatted_reply, thread_ts=ts)
    logger.info(f"Finished processing")


@app.post("/")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    # Get the request body and headers
    logger.info("Received request")
    body = await request.body()
    headers = request.headers
    data = process_slack_events(body, headers)

    if "challenge" in data:
        return JSONResponse(content=data["challenge"])

    action = get_action(data["event"]["text"], os.getenv("SLACK_BOT_ID"))
    if "thread_ts" in data["event"]:
        logger.info("Processing started")
        background_tasks.add_task(run_slack_ai, action, data["event"]["channel"], data["event"]["thread_ts"])
    return JSONResponse(content="Processing started")


@app.get("/")
async def index():
    return "Slack GPT Bot"


if __name__ == "__main__":
    # for local debugging
    import json

    with open("data.json") as f:
        data = json.load(f)

    _, action = get_action(data["event"]["text"], os.getenv("SLACK_BOT_ID"))

    if "thread_ts" in data["event"]:
        run_slack_ai(action, data["event"]["channel"], data["event"]["thread_ts"])
