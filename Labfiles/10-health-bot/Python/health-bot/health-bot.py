from dotenv import load_dotenv
from uuid import uuid4
import os
import asyncio
import aiohttp


class DirectLineToken:
    def __init__(self, conversation_id, token, expires_in):
        self.conversation_id = conversation_id
        self.token = token
        self.expires_in = expires_in


class ChatConfig:
    def __init__(self, token, userId):
        self.token = token
        self.userId = userId


async def get_direct_line_token(session):
    url = "https://directline.botframework.com/v3/directline/tokens/generate"
    headers = {"Authorization": f"Bearer {direct_line_secret}"}
    user_id = f"dl_{uuid4()}"
    data = {"User": {"Id": user_id}}
    async with session.post(url, headers=headers, json=data) as response:
        if response.status == 200:
            response_json = await response.json()
            return DirectLineToken(response_json["conversationId"], response_json["token"],
                                   response_json["expires_in"]), user_id
        else:
            raise Exception(f"Error getting DirectLine token: {response.status}")


async def new_conversation(session, config):
    url = "https://directline.botframework.com/v3/directline/conversations"
    headers = {"Authorization": f"Bearer {config.token}"}
    async with session.post(url, headers=headers) as response:
        if response.status == 201:
            response_json = await response.json()
            return (
                response_json["conversationId"],
                response_json["token"],
                response_json["expires_in"],
                response_json["streamUrl"],
            )
        else:
            print(f"Error opening new conversation: {response.status}")
            return None


async def send_activity(session, config, conversation_id, activity):
    url = f"https://directline.botframework.com/v3/directline/conversations/{conversation_id}/activities"
    headers = {"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"}
    async with session.post(url, headers=headers, json=activity) as response:
        return response.status == 200


async def get_activities(session, config, conversation_id, watermark=None):
    url = f"https://directline.botframework.com/v3/directline/conversations/{conversation_id}/activities"
    params = {"watermark": None} if watermark else {}
    headers = {"Authorization": f"Bearer {config.token}"}
    async with session.get(url, headers=headers, params=params) as response:
        if response.status == 200:
            response_json = await response.json()
            return response_json["activities"], response_json.get("watermark")
        else:
            print(f"Error retrieving activities: {response.status}")
            return None


async def interaction(session, config, conversation_id, user_id, text):
    activity = {"type": "message", "from": {"id": user_id}, "text": text}
    send_success = await send_activity(session, config, conversation_id, activity)
    if send_success:
        print("Successfully sent message to the bot.")
    activities, _ = await get_activities(session, config, conversation_id)
    if activities:
        print("Received messages from the bot:")
        for activity in activities:
            print(f"  - Type: {activity['type']}")
            print(f"    - From: {activity['from']['id']}")
            print(f"    - Text: {activity.get('text')}")


async def test_bot():
    try:
        async with aiohttp.ClientSession() as session:
            token, user_id = await get_direct_line_token(session)
            config = ChatConfig(token.token, user_id)
            conversation_info = await new_conversation(session, config)
            if conversation_info:
                conversation_id, _, _, _ = conversation_info
                await interaction(session, config, conversation_id, user_id, "")
                user_text = input("Enter your message to the bot: ")
                await interaction(session, config, conversation_id, user_id, user_text)
            else:
                print("Failed to open new conversation.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    load_dotenv()
    direct_line_secret = os.getenv('DIRECT_LINE_SECRET')
    asyncio.run(test_bot())
