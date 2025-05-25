from dotenv import load_dotenv
from uuid import uuid4
import os
import requests


class DirectLineToken:
    def __init__(self, conversation_id, token, expires_in):
        self.conversation_id = conversation_id
        self.token = token
        self.expires_in = expires_in


class ChatConfig:
    def __init__(self, token, userId):
        self.token = token
        self.userId = userId


def get_direct_line_token():
    url = "https://directline.botframework.com/v3/directline/tokens/generate"
    headers = {"Authorization": f"Bearer {direct_line_secret}"}
    user_id = f"dl_{uuid4()}"
    data = {"User": {"Id": user_id}}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        return DirectLineToken(response_json["conversationId"], response_json["token"],
                               response_json["expires_in"]), user_id
    else:
        raise Exception(f"Error getting DirectLine token: {response.status_code}")


def new_conversation(config):
    url = "https://directline.botframework.com/v3/directline/conversations"
    headers = {"Authorization": f"Bearer {config.token}"}
    response = requests.post(url, headers=headers)
    if response.status_code == 201:
        response_json = response.json()
        return (
            response_json["conversationId"],
            response_json["token"],
            response_json["expires_in"],
            response_json["streamUrl"],
        )
    else:
        print(f"Error opening new conversation: {response.status_code}")
        return None


def send_activity(config, conversation_id, activity):
    url = f"https://directline.botframework.com/v3/directline/conversations/{conversation_id}/activities"
    headers = {"Authorization": f"Bearer {config.token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=activity)
    return response.status_code == 200


def get_activities(config, conversation_id, watermark=None):
    url = f"https://directline.botframework.com/v3/directline/conversations/{conversation_id}/activities"
    params = {"watermark": None} if watermark else {}
    headers = {"Authorization": f"Bearer {config.token}"}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        response_json = response.json()
        return response_json["activities"], response_json.get("watermark")
    else:
        print(f"Error retrieving activities: {response.status_code}")
        return None


def interaction(config, conversation_id, user_id, text):
    activity = {"type": "message", "from": {"id": user_id}, "text": text}
    send_success = send_activity(config, conversation_id, activity)
    if send_success:
        print("Successfully sent message to the bot.")
    print_activities(config, conversation_id)


def print_activities(config, conversation_id):
    activities, _ = get_activities(config, conversation_id)
    if activities:
        print("Received messages from the bot:")
        for activity in activities:
            print(f"  - Type: {activity['type']}")
            print(f"    - From: {activity['from']['id']}")
            print(f"    - Text: {activity.get('text')}")


def test_bot():
    try:
        token, user_id = get_direct_line_token()
        config = ChatConfig(token.token, user_id)
        conversation_info = new_conversation(config)
        if conversation_info:
            conversation_id, _, _, _ = conversation_info
            # interaction(config, conversation_id, user_id, "")
            print_activities(config, conversation_id)
            user_text = input("Enter your message to the bot: ")
            interaction(config, conversation_id, user_id, user_text)
        else:
            print("Failed to open new conversation.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    load_dotenv()
    direct_line_secret = os.getenv('DIRECT_LINE_SECRET')
    test_bot()