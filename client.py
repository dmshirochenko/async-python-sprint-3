import requests
import json
from typing import Optional


class ChatClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.token: Optional[str] = None

    def connect(self) -> None:
        try:
            url_to_send = self.server_url + "/connect"
            response = requests.post(url_to_send, data='Initial request')
            response.raise_for_status()
            self.token = response.headers.get('Authorization')
            if self.token:
                print("Connected successfully.")
            else:
                print("Authorization token not received.")
            return response
        except requests.RequestException as e:
            print(f"Failed to connect: {e}")

    def get_chat_history(self, params=None) -> None:
        try:
            url_to_send = self.server_url + "/status"
            headers = {'Authorization': self.token} if self.token else {}
            response = requests.get(url_to_send, headers=headers, params=params)
            response.raise_for_status()
            print(response.text)
            return response
        except requests.RequestException as e:
            print(f"Failed to retrieve chat history: {e}")

    def post_message(self, message: str, message_type: str, recipient_id: int = None) -> None:
        try:
            if message_type == 'private':
                url_to_send = self.server_url + "/send-private"
                data = json.dumps({"text": message, "recipient_id": recipient_id})
            else:
                url_to_send = self.server_url + "/send"
                data = json.dumps({"text": message})

            headers = {'Authorization': self.token, 'Content-Type': 'application/json'} if self.token else {}
            response = requests.post(url_to_send, data=data, headers=headers)
            response.raise_for_status()
            print(response.text)
            return response
        except requests.RequestException as e:
            print(f"Failed to send message: {e}")


def main():
    server_url = "http://127.0.0.1:8000"
    client = ChatClient(server_url)
    client.connect()

    while True:
        action = input("Choose an action: 'get' to view chat history, 'post' to send a message, 'quit' to exit: ")
        if action.lower() == "get":
            params_dct = {}
            message_type = input("Enter message type (common/private): ")
            if message_type == "common":
                params_dct['chat_type'] = 'common'
                client.get_chat_history(params_dct)
            elif message_type == "private":
                params_dct['chat_type'] = 'private'
                recipient_id = input("Enter user_id: ")
                params_dct['recipient_id'] = recipient_id
                client.get_chat_history(params_dct)
            else:
                print("Wrong message type! You need to select between common/private...")
        elif action.lower() == "post":
            message_type = input("Enter message type (common/private): ")
            if message_type == "common":
                message = input("Enter your message: ")
                client.post_message(message, message_type)
            elif message_type == "private":
                recipient_id = input("Enter user_id (to whom send): ")
                message = input("Enter your message: ")
                client.post_message(message, message_type, recipient_id)
            else:
                print("Wrong message type! You need to select between common/private...")
        elif action.lower() == "quit":
            break
        else:
            print("Invalid action. Please choose 'get', 'post', or 'quit'.")


if __name__ == "__main__":
    main()
