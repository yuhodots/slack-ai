def template(conversation):
    system_content = "You are an AI bot for summarization converstaion in Slack message."
    user_content = f"""
Please summarize the following conversation described in 'CONVERSATION' by following the several rules described in 'RULES'. You must follow the response format shown in 'RESPONSE FORMAT'.
In the conversation, `<@usercode>` format is used for calling a user in Slack.  

CONVERSATION:
```
{conversation}
```

RULES:
1. Summarize in Korean. This is the most important rule. You have to follow this rule. But please show user name in English (i.e., *user name*).
2. In '전체 요약' section, summarize conversation under four lines.
3. In '인물별 요약' section, make a toggle for each person and summarize their arguments as one sentence as much as possible.
4. You can add '향후 필요한 조치' section if there is anything you need to do in the future as a conclusion to the conversation. This section is an optional.
    
RESPONSE FORMAT:
*[전체 요약]* 
• ...
• ...
\n\n
*[인물별 요약]*
• *user name*: ...
• *user name*: ...
\n\n
*[향후 필요한 조치]* <This section is optional>
• ...
• ...
"""
    return {
        "system": system_content,
        "user": user_content
    }
