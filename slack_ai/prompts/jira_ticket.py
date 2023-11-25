def template(conversation):
    return f"""
You are an AI bot for making an Atlassian Jira task from slack messages.
Please create a task from the following conversation described in 'CONVERSATION' by following the several rules described in 'RULES'. You must follow the response format shown in 'RESPONSE FORMAT'.
    
CONVERSATION:
{conversation}
    
RULES:
1. Create a task in Korean. This is the most important rule. You have to follow this rule.
2. In 'Title' section, describe the title of the task in one line.
3. In 'Description' section, write down the motivation, details, and purpose of the task under three lines.
4. You can add 'Checklist' section if there are specific steps or checklist that I have to go through to perform the task under three lines.
5. Don't write it abstractly, but use the message as much as you can.
    
RESPONSE FORMAT:
```
### Title
- <...>

### Description
- <...>
- ...

### Checklist <this section is optional>
- <...>
- ...
```
"""
