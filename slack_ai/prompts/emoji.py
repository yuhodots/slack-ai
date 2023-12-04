def template(conversation):
    system_content = "You are an AI bot for generating emoji."
    user_content = f"""
Please put the appropriate emojis next to the words in the following Slack message.

{conversation}
"""
    return {
        "system": system_content,
        "user": user_content
    }
