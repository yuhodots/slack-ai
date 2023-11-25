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


def process_slack_events(body, headers, verbose=True):
    if verbose:
        print('BODY', body)
        print('HEADER', headers)

    # Avoid replay attacks
    if abs(time.time() - int(headers.get('X-Slack-Request-Timestamp'))) > 60 * 5:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    if not signature_verifier.is_valid(
            body=body,
            timestamp=headers.get("X-Slack-Request-Timestamp"),
            signature=headers.get("X-Slack-Signature")):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = json.loads(body)
    return data


def process_user_message(user_message, slack_bot_id):
    user_message = user_message.replace(f'{slack_bot_id}', '').strip()
    action = None
    return user_message, action


def run_slack_ai(user_message, options, channel, thread_ts):
    raise NotImplementedError


@app.post("/")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    # Get the request body and headers
    body = await request.body()
    headers = request.headers
    data = process_slack_events(body, headers)

    if 'challenge' in data:
        return JSONResponse(content=data['challenge'])

    user_message, options = process_user_message(data['event']['text'], os.getenv("SLACK_BOT_ID"))
    event = data['event']
    thread_ts = event['thread_ts'] if 'thread_ts' in event else event['ts']
    background_tasks.add_task(run_slack_ai, user_message, options, event['channel'], thread_ts)
    return JSONResponse(content="Launched SlackGPT.")


@app.get("/")
async def index():
    return 'Slack GPT Bot'
