# tests/test_chat_client.py
import sys
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from client import ChatClient


def test_user_connections(server_url):
    # Create two users
    user1 = ChatClient(server_url)
    user2 = ChatClient(server_url)

    response1 = user1.connect()
    response2 = user2.connect()

    response1_json = json.loads(response1.text)
    response2_json = json.loads(response2.text)

    print(response1_json, response2_json)
    assert response1_json['status'] == "success", "User 1 failed to connect"
    assert response2_json['status'] == "success", "User 2 failed to connect"

    assert response1_json['user_id'] is not None, "User 1 did not receive a user_id"
    assert response2_json['user_id'] is not None, "User 2 did not receive a user_id"

    user1.user_id = response1_json['user_id']
    user2.user_id = response2_json['user_id']

    return user1, user2 

def test_send_public_message(server_url):
    user1, user2 = test_user_connections(server_url)

    # Test sending a public message from user1
    message = "Hello, everyone!"
    response = user1.post_message(message, "common")
    assert response.status_code == 200, "User 1 failed to send a public message"

    # Test if user2 received the message
    history = user2.get_chat_history({"chat_type": "common"})
    assert message in history.text, "User 2 did not receive the public message"

def test_private_message_exchange(server_url):
    user1, user2 = test_user_connections(server_url)

    # Test sending a private message from user1 to user2
    message = "Hello from User 1"
    response = user1.post_message(message, "private", recipient_id=user2.user_id)
    assert response.status_code == 200, "User 1 failed to send a private message"

    # Test if user2 received the message
    history = user2.get_chat_history({"chat_type": "private", "recipient_id": user1.user_id})
    assert message in history.text, "User 2 did not receive the message"

