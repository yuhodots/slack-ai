import os
import time
import json
from collections import defaultdict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
from slack_ai.prompts import ACTION_LIST, jira_ticket, summary


# load environment variables
load_dotenv('/slack_ai/.env')

# set slack client
rate_limit_handler = RateLimitErrorRetryHandler(max_retry_count=1)
signature_verifier = SignatureVerifier(signing_secret=os.environ["SLACK_SIGNING_SECRET"])
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
client.retry_handlers.append(rate_limit_handler)
thread_ts2pids = defaultdict(list)

# run fastapi
app = FastAPI()


def process_slack_events(body, headers):
    # Avoid replay attacks
    if abs(time.time() - int(headers.get('X-Slack-Request-Timestamp'))) > 60 * 5:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    if not signature_verifier.is_valid(
            body=body,
            timestamp=headers.get("X-Slack-Request-Timestamp"),
            signature=headers.get("X-Slack-Signature")
        ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = json.loads(body)
    return data


def get_action(user_message, slack_bot_id):
    user_message = user_message.replace(f'<@{slack_bot_id}>', '').strip()

    # select action
    if user_message.startswith('!'):
        action = user_message[1:]
        if action not in ACTION_LIST:
            raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
        return user_message, action
    else:
        return user_message, None
    

def get_messages_from_current_thread(channel, ts):
    # get messages from current thread
    messages = []
    cursor = None
    while True:
        response = client.conversations_replies(channel=channel, ts=ts, cursor=cursor, limit=200)
        messages += response['messages']
        if not response['has_more']:
            break
        cursor = response['response_metadata']['next_cursor']
    return messages


def process_conversation(messages):
    # process current thread messages to conversation (user_name: message)
    conversation = []
    for message in messages:
        if 'user' in message:
            conversation.append(f"{message['user']}: {message['text']}")
    return '\n'.join(conversation)


def run_slack_ai(action, channel, ts):
    messages = get_messages_from_current_thread(channel, ts)
    conversation = process_conversation(messages)
    action_func = jira_ticket if action == 'jira_ticket' else summary
    response = action_func(conversation)
    client.chat_postMessage(channel=channel, ts=ts, text=response)


@app.post("/")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    # Get the request body and headers
    body = await request.body()
    headers = request.headers
    data = process_slack_events(body, headers)

    if 'challenge' in data:
        return JSONResponse(content=data['challenge'])

    action = get_action(data['event']['text'], os.getenv("SLACK_BOT_ID"))
    ts = data['event']['thread_ts'] if 'thread_ts' in data['event'] else data['event']['ts']
    background_tasks.add_task(run_slack_ai, action, data['event']['channel'], ts)
    return JSONResponse(content="Processing started")


@app.get("/")
async def index():
    return 'Slack GPT Bot'
